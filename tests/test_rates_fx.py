import unittest
from pathlib import Path

from src.rates_fx import credit_spreads, fx_performance, load_rates_fx, rates_fx_as_of, yield_curve


ROOT = Path(__file__).resolve().parents[1]


class RatesFxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frame = load_rates_fx(ROOT / "data" / "fixtures" / "rates_fx.csv")

    def test_fixture_has_explicit_units_and_quote_directions(self):
        fx = self.frame.loc[self.frame.kind.eq("fx_spot")]
        self.assertTrue((fx.unit == fx.quote_currency + " per " + fx.base_currency).all())

    def test_cutoff_selects_latest_available_observation(self):
        early = rates_fx_as_of(self.frame, "2026-01-05")
        self.assertAlmostEqual(early.set_index("instrument").loc["UST 10Y", "value"], 4.50)
        late = rates_fx_as_of(self.frame, "2026-01-31")
        self.assertAlmostEqual(late.set_index("instrument").loc["UST 10Y", "value"], 4.55)

    def test_yield_curve_preserves_tenor_and_percent_unit(self):
        curve = yield_curve(self.frame, "2026-01-31")
        self.assertEqual(set(curve.tenor), {"2Y", "10Y"})
        self.assertEqual(set(curve.unit), {"percent"})

    def test_credit_spread_is_hand_checked_in_basis_points(self):
        spreads = credit_spreads(self.frame, "2026-01-31")
        self.assertAlmostEqual(spreads.iloc[0].spread_bps, 140.0)

    def test_fx_return_and_direction_are_hand_checked(self):
        fx = fx_performance(self.frame, "2026-01-31").set_index("instrument")
        self.assertAlmostEqual(fx.loc["EUR/USD", "base_return"], 0.02)
        self.assertEqual(fx.loc["EUR/USD", "interpretation"], "EUR strengthened versus USD")
        self.assertAlmostEqual(fx.loc["USD/NGN", "base_return"], 0.02)
        self.assertEqual(fx.loc["USD/NGN", "unit"], "NGN per USD")

    def test_missing_history_returns_no_fx_performance(self):
        self.assertTrue(fx_performance(self.frame, "2026-01-05").empty)


if __name__ == "__main__":
    unittest.main()
