import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from operations import create_verified_backup, database_manifest, operational_health, restore_verified_backup
from persistence import EvidenceStore


class OperationsRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT / "data/runtime").mkdir(parents=True, exist_ok=True)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "data/runtime")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "evidence.db"
        self.store = EvidenceStore(self.source)
        self.source_id = self.store.register_source(
            "Example", "https://example.org/feed.xml", source_id="example", now="2026-01-01T00:00:00Z"
        )
        articles = pd.DataFrame({
            "article_id": ["one"], "headline": ["Policy unchanged"],
            "url": ["https://example.org/one"], "published_at": ["2026-01-01T00:00:00Z"],
            "available_at": ["2026-01-02T00:00:00Z"],
        })
        self.store.record_snapshot(self.source_id, b"<feed>one</feed>", articles, retrieved_at="2026-01-02T00:00:00Z")

    def test_manifest_checks_integrity_schema_counts_and_hash(self):
        manifest = database_manifest(self.source)
        self.assertEqual(manifest["integrity"], "ok")
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(manifest["row_counts"]["snapshots"], 1)
        self.assertEqual(len(manifest["sha256"]), 64)

    def test_backup_and_restore_preserve_schema_and_row_counts(self):
        backup = self.root / "backup.db"
        restored = self.root / "restored.db"
        backup_report = create_verified_backup(self.source, backup)
        restore_report = restore_verified_backup(backup, restored)
        self.assertEqual(backup_report["status"], "verified")
        self.assertEqual(restore_report["status"], "verified")
        self.assertEqual(database_manifest(self.source)["row_counts"], database_manifest(restored)["row_counts"])

    def test_backup_never_overwrites_existing_target(self):
        target = self.root / "backup.db"
        target.write_bytes(b"keep")
        with self.assertRaises(FileExistsError):
            create_verified_backup(self.source, target)
        self.assertEqual(target.read_bytes(), b"keep")

    def test_health_surfaces_attempt_counts_and_latest_time(self):
        health = operational_health(self.source)
        self.assertEqual(health["status"], "healthy")
        self.assertEqual(health["attempts"], 1)
        self.assertEqual(health["failed_attempts"], 0)
        self.assertEqual(health["latest_attempt_at"], "2026-01-02T00:00:00+00:00")

    def test_missing_and_corrupt_databases_fail_visibly(self):
        self.assertEqual(operational_health(self.root / "missing.db")["status"], "not_initialised")
        corrupt = self.root / "corrupt.db"
        corrupt.write_bytes(b"not sqlite")
        with self.assertRaises(sqlite3.DatabaseError):
            database_manifest(corrupt)


if __name__ == "__main__":
    unittest.main()
