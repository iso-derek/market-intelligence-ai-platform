"""D3.1 deterministic entity-resolution acceptance tests."""
from pathlib import Path
import sys
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from entities import (  # noqa: E402
    RESOLUTION_VERSION,
    load_entity_registry,
    resolution_summary,
    resolve_news_entities,
    resolve_text,
)


class EntityResolutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_entity_registry(ROOT / "data" / "fixtures" / "entity_registry.csv")

    def test_canonical_name_alias_and_ticker_resolve(self):
        for text in ["Apple Inc. raises outlook", "Apple raises outlook", "$AAPL raises outlook"]:
            row = resolve_text(text, self.registry)[0]
            self.assertEqual(row["resolution_status"], "resolved")
            self.assertEqual(row["entity_id"], "ent_aapl")
            self.assertEqual(row["ticker"], "AAPL")

    def test_longest_alias_prevents_false_ambiguity(self):
        row = resolve_text("Alpha Industries reports results", self.registry)[0]
        self.assertEqual(row["resolution_status"], "resolved")
        self.assertEqual(row["entity_id"], "ent_alp")
        self.assertEqual(row["matched_alias"], "alpha industries")

    def test_shared_alias_is_explicitly_ambiguous(self):
        row = resolve_text("Alpha reports results", self.registry)[0]
        self.assertEqual(row["resolution_status"], "ambiguous")
        self.assertEqual(row["candidate_ids"], "ent_alp|ent_axc")
        self.assertEqual(row["entity_id"], "")

    def test_unknown_text_remains_unknown(self):
        row = resolve_text("Unlisted Foods reports results", self.registry)[0]
        self.assertEqual(row["resolution_status"], "unknown")
        self.assertEqual(row["candidate_ids"], "")

    def test_multiple_distinct_companies_resolve_independently(self):
        rows = resolve_text("Apple partners with Microsoft", self.registry)
        self.assertEqual({row["ticker"] for row in rows}, {"AAPL", "MSFT"})
        self.assertTrue(all(row["resolution_status"] == "resolved" for row in rows))

    def test_case_variant_aliases_do_not_duplicate_one_entity(self):
        row = resolve_text("NVIDIA reports results", self.registry)[0]
        self.assertEqual(row["resolution_status"], "resolved")
        self.assertEqual(row["ticker"], "NVDA")

    def test_word_boundaries_prevent_substring_matches(self):
        self.assertEqual(resolve_text("Pineapple demand improves", self.registry)[0]["resolution_status"], "unknown")

    def test_frame_preserves_one_outcome_per_record_and_version(self):
        news = pd.DataFrame(
            {
                "article_id": ["a", "b", "c"],
                "headline": ["Apple gains", "Alpha reports", "Unlisted Foods reports"],
            }
        )
        resolved = resolve_news_entities(news, self.registry)
        self.assertEqual(set(resolved.record_id), {"a", "b", "c"})
        self.assertEqual(set(resolved.resolution_version), {RESOLUTION_VERSION})
        self.assertEqual(resolution_summary(resolved), {"resolved": 1, "ambiguous": 1, "unknown": 1})

    def test_registry_rejects_duplicate_entity_ids(self):
        duplicate = self.registry.copy()
        duplicate.loc[1, "entity_id"] = duplicate.loc[0, "entity_id"]
        path = ROOT / "data" / "runtime" / "duplicate_entities.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        duplicate.to_csv(path, index=False)
        try:
            with self.assertRaisesRegex(ValueError, "unique"):
                load_entity_registry(path)
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
