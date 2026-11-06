"""D4.1 filings corpus integrity and point-in-time tests."""
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from filings import filings_as_of, load_filing_manifest, load_filings_corpus  # noqa: E402


class FilingsCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ROOT / "data" / "filings"
        cls.documents, cls.passages = load_filings_corpus(cls.root)

    def test_manifest_and_all_document_hashes_verify(self):
        self.assertEqual(len(self.documents), 3)
        self.assertTrue(self.documents.hash_verified.all())
        self.assertTrue(self.documents.sha256.str.fullmatch(r"[0-9a-f]{64}").all())

    def test_page_section_period_and_passage_hashes_are_preserved(self):
        self.assertEqual(len(self.passages), 18)
        self.assertEqual(set(self.passages.page), {1, 2, 3})
        self.assertTrue(self.passages.section.str.strip().ne("").all())
        self.assertTrue(self.passages.text_sha256.str.fullmatch(r"[0-9a-f]{64}").all())
        self.assertTrue(self.passages.period_end.notna().all())

    def test_point_in_time_cutoff_excludes_later_filings(self):
        documents, passages = filings_as_of(self.documents, self.passages, "2026-01-23")
        self.assertEqual(documents.document_id.tolist(), ["filing-bet-2025"])
        self.assertEqual(set(passages.document_id), {"filing-bet-2025"})

    def test_later_cutoff_includes_all_reports(self):
        documents, passages = filings_as_of(self.documents, self.passages, "2026-03-01")
        self.assertEqual(len(documents), 3)
        self.assertEqual(len(passages), 18)

    def _copy_corpus(self, parent: Path) -> Path:
        target = parent / "filings"
        shutil.copytree(self.root, target)
        return target

    def test_hash_mismatch_is_rejected(self):
        runtime = ROOT / "data" / "runtime"
        runtime.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=runtime) as directory:
            corpus = self._copy_corpus(Path(directory))
            with (corpus / "alpha_2025_annual.txt").open("a", encoding="utf-8") as handle:
                handle.write("\nTampered")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                load_filings_corpus(corpus)

    def test_path_traversal_is_rejected(self):
        runtime = ROOT / "data" / "runtime"
        runtime.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=runtime) as directory:
            corpus = self._copy_corpus(Path(directory))
            manifest = pd.read_csv(corpus / "manifest.csv")
            manifest.loc[0, "file_name"] = "../outside.txt"
            manifest.to_csv(corpus / "manifest.csv", index=False)
            with self.assertRaisesRegex(ValueError, "inside the corpus root"):
                load_filing_manifest(corpus)

    def test_invalid_page_sequence_is_rejected_even_with_updated_hash(self):
        runtime = ROOT / "data" / "runtime"
        runtime.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=runtime) as directory:
            corpus = self._copy_corpus(Path(directory))
            path = corpus / "beta_2025_annual.txt"
            path.write_text(path.read_text(encoding="utf-8").replace("=== PAGE 2 ===", "=== PAGE 4 ==="), encoding="utf-8")
            import hashlib
            manifest = pd.read_csv(corpus / "manifest.csv")
            manifest.loc[manifest.document_id.eq("filing-bet-2025"), "sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            manifest.to_csv(corpus / "manifest.csv", index=False)
            with self.assertRaisesRegex(ValueError, "consecutive"):
                load_filings_corpus(corpus)


if __name__ == "__main__":
    unittest.main()
