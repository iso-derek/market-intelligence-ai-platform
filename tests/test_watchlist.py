"""D8.1 analyst-watchlist calculation and search tests."""
from pathlib import Path
import sys
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from entities import load_entity_registry  # noqa: E402
from market_data import FixtureProvider  # noqa: E402
from watchlist import (  # noqa: E402
    company_universe,
    normalized_performance,
    search_companies,
    snapshot_hash,
    watchlist_snapshot,
)


class WatchlistTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ROOT / "data" / "fixtures"
        cls.provider = FixtureProvider(cls.root)
        cls.registry = load_entity_registry(cls.root / "entity_registry.csv")
        cls.universe = company_universe(cls.registry, cls.provider.prices(), "2026-03-01")

    def test_universe_is_limited_to_companies_with_price_coverage(self):
        self.assertEqual(set(self.universe.ticker), {"ALP", "BET", "GAM"})
        self.assertNotIn("AAPL", set(self.universe.ticker))

    def test_search_uses_complete_ticker_name_sector_and_alias_tokens(self):
        self.assertEqual(search_companies(self.universe, "ALP").ticker.tolist(), ["ALP"])
        self.assertEqual(search_companies(self.universe, "Beta Retail").ticker.tolist(), ["BET"])
        self.assertEqual(search_companies(self.universe, "Technology").ticker.tolist(), ["GAM"])
        self.assertTrue(search_companies(self.universe, "LP").empty)

    def test_sector_filter_and_no_match_are_explicit(self):
        self.assertEqual(search_companies(self.universe, sectors=["Consumer"]).ticker.tolist(), ["BET"])
        self.assertTrue(search_companies(self.universe, "bank").empty)

    def test_snapshot_matches_hand_checked_market_and_fundamental_values(self):
        snapshot = watchlist_snapshot(
            self.provider.prices(), self.provider.fundamentals(), ["ALP", "GAM"], "2026-01-31"
        ).set_index("ticker")
        self.assertAlmostEqual(snapshot.loc["ALP", "cumulative_return"], 0.08)
        self.assertAlmostEqual(snapshot.loc["ALP", "net_margin"], 0.10)
        self.assertAlmostEqual(snapshot.loc["GAM", "current_ratio"], 2.5)
        self.assertEqual(snapshot.loc["GAM", "filing_unit"], "millions")

    def test_snapshot_respects_report_restatement_cutoff(self):
        early = watchlist_snapshot(
            self.provider.prices(), self.provider.fundamentals(), ["ALP"], "2026-01-31"
        )
        late = watchlist_snapshot(
            self.provider.prices(), self.provider.fundamentals(), ["ALP"], "2026-03-01"
        )
        self.assertEqual(early.net_income.item(), 100)
        self.assertEqual(late.net_income.item(), 90)

    def test_normalized_performance_starts_each_company_at_100(self):
        indexed = normalized_performance(self.provider.prices(), ["ALP", "BET"], "2026-01-31")
        starts = indexed.sort_values("date").groupby("ticker").first()
        self.assertTrue(starts.indexed_close.eq(100).all())
        self.assertAlmostEqual(indexed.loc[indexed.ticker.eq("ALP"), "indexed_close"].iloc[-1], 108)

    def test_invalid_and_empty_selections_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "select at least one"):
            watchlist_snapshot(self.provider.prices(), self.provider.fundamentals(), [], "2026-03-01")
        with self.assertRaisesRegex(ValueError, "XYZ"):
            watchlist_snapshot(self.provider.prices(), self.provider.fundamentals(), ["XYZ"], "2026-03-01")

    def test_snapshot_hash_is_stable_and_sensitive_to_cutoff(self):
        first = watchlist_snapshot(
            self.provider.prices(), self.provider.fundamentals(), ["GAM", "ALP"], "2026-01-31"
        )
        second = first.sample(frac=1, random_state=7)
        changed = first.copy()
        changed["cutoff"] = pd.Timestamp("2026-03-01T00:00:00Z")
        self.assertEqual(snapshot_hash(first), snapshot_hash(second))
        self.assertNotEqual(snapshot_hash(first), snapshot_hash(changed))


if __name__ == "__main__":
    unittest.main()
