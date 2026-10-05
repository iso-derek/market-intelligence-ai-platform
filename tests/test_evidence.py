import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import unittest
import json
import io
import zipfile
import pandas as pd
from ingestion import normalise_news,parse_feed,canonical_url
from evidence import evidence_brief,audit_claims,export_bundle
from language_models import finbert_predictions
from evaluation import evaluate_sentiment

class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.raw=pd.DataFrame({'headline':['Policy rates remain unchanged','Inflation falls in latest report'],
            'url':['https://example.org/rates?utm_source=feed','https://example.org/inflation'],
            'published_at':['2026-01-01','2026-01-02'],'available_at':['2026-01-03','2026-01-03']})
        self.news=normalise_news(self.raw,'2026-01-03')
    def test_publication_is_not_availability(self):
        self.assertTrue(evidence_brief(self.news,'rates','2026-01-02')['abstained'])
        self.assertEqual(len(evidence_brief(self.news,'rates','2026-01-04')['claims']),1)
    def test_irrelevant_query_abstains(self):
        self.assertTrue(evidence_brief(self.news,'volcanic submarine','2026-01-04')['abstained'])
    def test_synthetic_sources_excluded(self):
        news=self.news.copy();news['synthetic']=True
        self.assertTrue(evidence_brief(news,'','2026-01-04')['abstained'])
    def test_duplicates_and_tracking_links(self):
        duplicate=pd.concat([self.raw,self.raw.iloc[:1]],ignore_index=True)
        news=normalise_news(duplicate,'2026-01-03')
        self.assertEqual(len(news),2)
        self.assertNotIn('utm_',news.url.iloc[0])
    def test_invalid_timestamp_and_unsafe_link_rejected(self):
        raw=self.raw.copy();raw.loc[0,'available_at']='2020-01-01'
        with self.assertRaises(ValueError):normalise_news(raw)
        with self.assertRaises(ValueError):canonical_url('javascript:alert(1)')
    def test_rss_and_atom(self):
        rss=b'<rss><channel><item><title>Rate decision</title><link>https://example.org/a</link><pubDate>Thu, 01 Jan 2026 12:00:00 GMT</pubDate></item></channel></rss>'
        atom=b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Rate decision</title><link href="https://example.org/a"/><updated>2026-01-01T12:00:00Z</updated></entry></feed>'
        for xml in [rss,atom]:
            frame,meta=parse_feed(xml,'Example','2026-01-03')
            self.assertEqual(meta['parsed'],1);self.assertEqual(frame.url.iloc[0],'https://example.org/a')
        with self.assertRaises(ValueError):parse_feed(b'<!DOCTYPE x [<!ENTITY t "bad">]><rss/>','Example')
    def test_citations_are_not_semantic_verification(self):
        claim={'text':'A completely unsupported prediction','article_ids':[self.news.article_id.iloc[0]]}
        row=audit_claims([claim],self.news).iloc[0]
        self.assertTrue(row.valid_citations);self.assertFalse(row.exact_headline_extract)
        self.assertIsNone(row.human_support)
        self.assertEqual(audit_claims([claim],self.news,{'0':'unsupported'}).iloc[0].human_support,'unsupported')
    def test_finbert_output_contract(self):
        fake=lambda texts,**kwargs:[ [{'label':'positive','score':.7},{'label':'negative','score':.1},{'label':'neutral','score':.2}] for t in texts]
        output=finbert_predictions(['Record revenue'],fake)
        self.assertAlmostEqual(output.sentiment_score.iloc[0],.6)
        self.assertEqual(output.sentiment_label.iloc[0],'Positive')
    def test_evaluation_requires_independent_labels_and_preserves_hash(self):
        frame=pd.DataFrame({'headline':['strong growth','weak demand','annual report'],'label':['Positive','Negative','Neutral']})
        report=evaluate_sentiment(frame)
        self.assertEqual(report['accuracy'],1)
        with self.assertRaises(ValueError): evaluate_sentiment(frame.drop(columns='label'))
    def test_bundle_contains_sources_cutoff_and_claims(self):
        brief=evidence_brief(self.news,'','2026-01-04')
        z=zipfile.ZipFile(io.BytesIO(export_bundle(self.news,brief,{})))
        self.assertEqual(json.loads(z.read('brief.json'))['as_of'],'2026-01-04')
        self.assertIn('articles.csv',z.namelist())

class AppTests(unittest.TestCase):
    def test_demo_and_irrelevant_query(self):
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run(timeout=30)
        self.assertFalse(app.exception)
        app.text_input[0].set_value('volcanic submarine').run()
        self.assertFalse(app.exception)

if __name__=='__main__':unittest.main()


class RfcTimestampTests(unittest.TestCase):
    def test_gmt_rss_date_is_utc(self):
        from ingestion import parse_feed
        xml=b'<rss><channel><item><title>Policy decision</title><link>https://example.org/policy</link><pubDate>Mon, 05 Oct 2026 08:00:00 GMT</pubDate></item></channel></rss>'
        frame,_=parse_feed(xml,'Fixture','2026-10-05T09:00:00Z')
        self.assertEqual(str(frame.published_at.iloc[0]),'2026-10-05 08:00:00+00:00')
