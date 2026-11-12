import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))

from ingestion import build_retrying_session,fetch_registered_feeds,normalise_news
from persistence import EvidenceStore


class FakeResponse:
    def __init__(self,content): self.content=content
    def raise_for_status(self): return None


class FakeSession:
    def __init__(self,content): self.content=content;self.calls=[]
    def get(self,url,**kwargs):
        self.calls.append((url,kwargs))
        return FakeResponse(self.content)


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store=EvidenceStore(Path(self.temp.name)/'evidence.db')
        self.source_id=self.store.register_source(
            'Example policy feed','https://example.org/feed.xml',source_id='example',
            now='2026-01-01T00:00:00Z')

    def frame(self,headline='Policy rates remain unchanged',available_at='2026-01-03T00:00:00Z'):
        return normalise_news(pd.DataFrame({
            'headline':[headline],
            'url':['https://example.org/policy'],
            'published_at':['2026-01-01T12:00:00Z'],
            'available_at':[available_at],
            'source':['Example policy feed'],
        }),available_at)

    def test_migration_and_registry_are_durable(self):
        self.assertEqual(self.store.schema_version(),1)
        reopened=EvidenceStore(self.store.path)
        sources=reopened.list_sources()
        self.assertEqual(sources.source_id.tolist(),['example'])
        self.assertTrue(bool(sources.enabled.iloc[0]))

    def test_snapshot_import_is_idempotent_but_attempts_remain_visible(self):
        first=self.store.record_snapshot(self.source_id,b'<feed>one</feed>',self.frame(),
                                         retrieved_at='2026-01-03T00:00:00Z')
        second=self.store.record_snapshot(self.source_id,b'<feed>one</feed>',self.frame(),
                                          retrieved_at='2026-01-04T00:00:00Z')
        self.assertTrue(first.inserted)
        self.assertFalse(second.inserted)
        self.assertEqual(len(self.store.snapshots()),1)
        self.assertEqual(len(self.store.attempts()),2)
        self.assertEqual(len(self.store.eligible_evidence('2026-01-10')),1)

    def test_revisions_are_preserved_without_changing_earlier_cutoffs(self):
        first=self.store.record_snapshot(self.source_id,b'<feed>version one</feed>',self.frame(),
                                         retrieved_at='2026-01-03T00:00:00Z')
        before=self.store.eligible_evidence('2026-01-04T00:00:00Z')
        self.store.record_snapshot(
            self.source_id,b'<feed>version two</feed>',
            self.frame('Policy rates remain unchanged after review','2026-01-05T00:00:00Z'),
            retrieved_at='2026-01-05T00:00:00Z')
        after=self.store.eligible_evidence('2026-01-04T00:00:00Z')
        latest=self.store.eligible_evidence('2026-01-06T00:00:00Z')
        pd.testing.assert_frame_equal(before,after)
        self.assertEqual(len(latest),2)
        self.assertEqual(self.store.replay_snapshot(first.snapshot_hash).headline.tolist(),
                         ['Policy rates remain unchanged'])

    def test_failure_is_visible_and_never_creates_synthetic_evidence(self):
        self.store.record_failure(self.source_id,'provider unavailable',
                                  checked_at='2026-01-03T00:00:00Z')
        source=self.store.list_sources().iloc[0]
        self.assertEqual(source.last_status,'failed')
        self.assertIn('provider unavailable',source.last_error)
        self.assertTrue(self.store.eligible_evidence('2026-01-04').empty)

    def test_snapshot_export_contains_payload_manifest_and_exact_articles(self):
        result=self.store.record_snapshot(self.source_id,b'<feed>one</feed>',self.frame(),
                                          retrieved_at='2026-01-03T00:00:00Z')
        archive=zipfile.ZipFile(io.BytesIO(self.store.export_snapshot(result.snapshot_hash)))
        self.assertEqual(set(archive.namelist()),{'manifest.json','articles.csv','snapshot.xml'})
        manifest=json.loads(archive.read('manifest.json'))
        self.assertEqual(manifest['snapshot_hash'],result.snapshot_hash)
        self.assertEqual(archive.read('snapshot.xml'),b'<feed>one</feed>')

    def test_registry_rejects_local_network_targets(self):
        with self.assertRaises(ValueError):
            self.store.register_source('Local','https://127.0.0.1/feed.xml')
        with self.assertRaises(ValueError):
            self.store.register_source('Insecure','http://example.org/feed.xml')

    def test_registered_fetch_persists_and_replays_feed(self):
        xml=(b'<rss><channel><item><title>Policy decision</title>'
             b'<link>https://example.org/policy</link>'
             b'<pubDate>Thu, 01 Jan 2026 12:00:00 GMT</pubDate>'
             b'</item></channel></rss>')
        session=FakeSession(xml)
        evidence,diagnostics=fetch_registered_feeds(
            self.store,[self.source_id],session=session,retrieved_at='2026-01-03T00:00:00Z')
        self.assertEqual(len(evidence),1)
        self.assertEqual(diagnostics[0]['status'],'ok')
        self.assertTrue(diagnostics[0]['new_snapshot'])
        self.assertEqual(session.calls[0][1]['timeout'],(5,20))

    def test_retry_policy_is_bounded_and_get_only(self):
        retry=build_retrying_session().get_adapter('https://').max_retries
        self.assertEqual(retry.total,2)
        self.assertEqual(retry.allowed_methods,frozenset({'GET'}))


if __name__=='__main__': unittest.main()
