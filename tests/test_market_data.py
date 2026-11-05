"""Hand-checked D2 finance, vintage, and provider-boundary tests."""
from pathlib import Path
import sys
import unittest

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_data import (  # noqa: E402
    FixtureProvider,
    MarketDataProvider,
    fundamental_ratios,
    fundamentals_as_of,
    macro_as_of,
    normalise_prices,
    price_performance,
    prices_as_of,
)


class MarketDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.provider = FixtureProvider(ROOT / "data" / "fixtures")

    def test_fixture_provider_satisfies_isolated_contract(self):
        self.assertIsInstance(self.provider, MarketDataProvider)
        self.assertEqual(set(self.provider.prices().instrument), {"ALP", "BET", "GAM"})
        self.assertNotIn("url", self.provider.prices().columns)

    def test_adjusted_prices_remove_split_discontinuity(self):
        alp = prices_as_of(self.provider.prices(), "2026-01-09")
        alp = alp.loc[alp.instrument.eq("ALP")].sort_values("date")
        raw_split_return = alp.raw_close.pct_change().iloc[3]
        adjusted_split_return = alp.adjusted_close.pct_change().iloc[3]
        self.assertAlmostEqual(raw_split_return, 53 / 104 - 1)
        self.assertAlmostEqual(adjusted_split_return, 53 / 52 - 1)
        self.assertLess(raw_split_return, -0.4)
        self.assertGreater(adjusted_split_return, 0)

    def test_hand_checked_return_and_volatility(self):
        performance = price_performance(self.provider.prices(), "2026-01-09")
        alp = performance.set_index("instrument").loc["ALP"]
        expected_returns = pd.Series([51 / 50 - 1, 52 / 51 - 1, 53 / 52 - 1, 54 / 53 - 1])
        self.assertAlmostEqual(alp.cumulative_return, 0.08)
        self.assertAlmostEqual(alp.annualized_volatility, expected_returns.std(ddof=1) * np.sqrt(252))
        self.assertEqual(alp.calendar, "XNYS")
        self.assertEqual(alp.currency, "USD")

    def test_future_prices_are_excluded_by_availability(self):
        frame = prices_as_of(self.provider.prices(), "2026-01-06T21:05:00Z")
        self.assertEqual(frame.loc[frame.instrument.eq("ALP"), "date"].max(), pd.Timestamp("2026-01-05T21:00:00Z"))

    def test_macro_revision_respects_historical_cutoff(self):
        early = macro_as_of(self.provider.macro(), "2026-01-31")
        late = macro_as_of(self.provider.macro(), "2026-03-01")
        key = lambda frame: frame.loc[
            frame.series_id.eq("CPI_YOY") & frame.observation_date.eq(pd.Timestamp("2025-12-01", tz="UTC")), "value"
        ].item()
        self.assertEqual(key(early), 2.9)
        self.assertEqual(key(late), 3.0)

    def test_restatement_does_not_leak_into_earlier_cutoff(self):
        early = fundamentals_as_of(self.provider.fundamentals(), "2026-01-31")
        late = fundamentals_as_of(self.provider.fundamentals(), "2026-03-01")
        select_income = lambda frame: frame.loc[
            frame.company.eq("ALP") & frame.metric.eq("net_income"), ["value", "report_version"]
        ].iloc[0]
        self.assertEqual(tuple(select_income(early)), (100, 1))
        self.assertEqual(tuple(select_income(late)), (90, 2))

    def test_partially_available_restatement_is_not_mixed_with_old_report(self):
        facts = self.provider.fundamentals()
        alp_v2 = facts.company.eq("ALP") & facts.report_version.eq(2)
        facts.loc[alp_v2 & facts.metric.ne("net_income"), "available_at"] = pd.Timestamp("2026-03-10T00:00:00Z")
        selected = fundamentals_as_of(facts, "2026-03-01")
        alp = selected.loc[selected.company.eq("ALP")]
        self.assertEqual(set(alp.report_version), {1})
        self.assertEqual(alp.loc[alp.metric.eq("net_income"), "value"].item(), 100)

    def test_hand_checked_peer_ratios_and_visible_dimensions(self):
        ratios = fundamental_ratios(self.provider.fundamentals(), "2026-01-31").set_index("company")
        self.assertAlmostEqual(ratios.loc["ALP", "net_margin"], 0.10)
        self.assertAlmostEqual(ratios.loc["ALP", "current_ratio"], 2.0)
        self.assertAlmostEqual(ratios.loc["ALP", "debt_to_equity"], 0.8)
        self.assertEqual(ratios.loc["ALP", "unit"], "millions")
        self.assertEqual(ratios.loc["ALP", "currency"], "USD")

    def test_validation_rejects_availability_before_market_date(self):
        invalid = self.provider.prices().copy()
        invalid.loc[0, "available_at"] = "2026-01-01T00:00:00Z"
        with self.assertRaisesRegex(ValueError, "availability"):
            normalise_prices(invalid)


if __name__ == "__main__":
    unittest.main()
