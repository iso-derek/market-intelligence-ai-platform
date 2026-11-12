"""D8.2 deterministic scenario arithmetic and guardrail tests."""
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_data import FixtureProvider  # noqa: E402
from scenario_analysis import ScenarioAssumptions, scenario_hash, stress_watchlist  # noqa: E402
from watchlist import watchlist_snapshot  # noqa: E402


class ScenarioAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.provider = FixtureProvider(ROOT / "data" / "fixtures")
        cls.early = watchlist_snapshot(
            cls.provider.prices(), cls.provider.fundamentals(), ["ALP", "BET", "GAM"], "2026-01-31"
        )
        cls.late = watchlist_snapshot(
            cls.provider.prices(), cls.provider.fundamentals(), ["ALP", "BET", "GAM"], "2026-03-01"
        )

    def test_neutral_scenario_preserves_all_company_metrics(self):
        result = stress_watchlist(self.early, ScenarioAssumptions())
        np.testing.assert_allclose(result.stressed_revenue, result.revenue)
        np.testing.assert_allclose(result.stressed_net_income, result.net_income)
        np.testing.assert_allclose(result.stressed_current_ratio, result.current_ratio)
        np.testing.assert_allclose(result.stressed_debt_to_equity, result.debt_to_equity)

    def test_hand_checked_downside_arithmetic(self):
        assumptions = ScenarioAssumptions(
            revenue_shock=-0.10,
            margin_shock_bps=-300,
            current_assets_shock=-0.10,
            current_liabilities_shock=0.10,
            debt_shock=0.20,
            equity_shock=-0.10,
        )
        alp = stress_watchlist(self.early, assumptions).set_index("ticker").loc["ALP"]
        self.assertAlmostEqual(alp.stressed_revenue, 900)
        self.assertAlmostEqual(alp.stressed_net_margin, 0.07)
        self.assertAlmostEqual(alp.stressed_net_income, 63)
        self.assertAlmostEqual(alp.net_income_change, -37)
        self.assertAlmostEqual(alp.stressed_current_ratio, 2.0 * 0.9 / 1.1)
        self.assertAlmostEqual(alp.stressed_debt_to_equity, 0.8 * 1.2 / 0.9)

    def test_point_in_time_restatement_changes_scenario_base(self):
        assumptions = ScenarioAssumptions(margin_shock_bps=-100)
        early = stress_watchlist(self.early, assumptions).set_index("ticker").loc["ALP"]
        late = stress_watchlist(self.late, assumptions).set_index("ticker").loc["ALP"]
        self.assertEqual(early.net_income, 100)
        self.assertEqual(late.net_income, 90)
        self.assertNotEqual(early.stressed_net_income, late.stressed_net_income)

    def test_results_preserve_dimensions_and_cutoff(self):
        result = stress_watchlist(self.early, ScenarioAssumptions(revenue_shock=0.05))
        self.assertEqual(set(result.filing_currency), {"USD"})
        self.assertEqual(set(result.filing_unit), {"millions"})
        self.assertEqual(result.cutoff.nunique(), 1)

    def test_assumption_bounds_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "revenue_shock"):
            ScenarioAssumptions(revenue_shock=-0.51)
        with self.assertRaisesRegex(ValueError, "margin_shock_bps"):
            ScenarioAssumptions(margin_shock_bps=2_001)
        with self.assertRaisesRegex(ValueError, "debt_shock"):
            ScenarioAssumptions(debt_shock=1.01)

    def test_missing_fundamental_values_are_rejected(self):
        incomplete = self.early.copy()
        incomplete.loc[0, "revenue"] = None
        with self.assertRaisesRegex(ValueError, "complete fundamental"):
            stress_watchlist(incomplete, ScenarioAssumptions())

    def test_scenario_hash_is_stable_and_assumption_sensitive(self):
        first_assumptions = ScenarioAssumptions(revenue_shock=-0.10)
        second_assumptions = ScenarioAssumptions(revenue_shock=-0.09)
        first = stress_watchlist(self.early, first_assumptions)
        reordered = first.sample(frac=1, random_state=11)
        second = stress_watchlist(self.early, second_assumptions)
        self.assertEqual(scenario_hash(first, first_assumptions), scenario_hash(reordered, first_assumptions))
        self.assertNotEqual(scenario_hash(first, first_assumptions), scenario_hash(second, second_assumptions))


if __name__ == "__main__":
    unittest.main()
