import unittest
from pathlib import Path

import pandas as pd

from src.event_study import event_session, market_adjusted_event_study
from src.market_data import FixtureProvider


ROOT = Path(__file__).resolve().parents[1]


class ReleaseAwareEventStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prices = FixtureProvider(ROOT / "data" / "fixtures").prices()
        cls.sessions = cls.prices.loc[cls.prices.instrument.eq("ALP"), "date"]

    def test_before_close_release_uses_same_session(self):
        self.assertEqual(event_session("2026-01-06T14:00:00Z", self.sessions), pd.Timestamp("2026-01-06T21:00:00Z"))

    def test_after_close_release_uses_next_session(self):
        self.assertEqual(event_session("2026-01-05T22:00:00Z", self.sessions), pd.Timestamp("2026-01-06T21:00:00Z"))

    def test_hand_checked_market_adjusted_window(self):
        summary, window = market_adjusted_event_study(
            self.prices, "ALP", "2026-01-06T14:00:00Z", "2026-01-31T23:59:59Z", 1, 1
        )
        self.assertEqual(window.relative_day.tolist(), [-1, 0, 1])
        self.assertAlmostEqual(summary["car"], window.abnormal_return.sum())
        self.assertEqual(summary["peer_count"], 2)
        self.assertEqual(summary["method"], "equal_weight_peer_market_adjusted")

    def test_cutoff_blocks_unavailable_post_event_prices(self):
        with self.assertRaisesRegex(ValueError, "insufficient observations"):
            market_adjusted_event_study(self.prices, "ALP", "2026-01-06T14:00:00Z", "2026-01-06T21:10:00Z", 1, 1)

    def test_invalid_window_and_unknown_instrument_fail_closed(self):
        with self.assertRaises(ValueError):
            market_adjusted_event_study(self.prices, "ALP", "2026-01-06", "2026-01-31", -1, 1)
        with self.assertRaises(ValueError):
            market_adjusted_event_study(self.prices, "UNKNOWN", "2026-01-06", "2026-01-31", 1, 1)

    def test_event_output_retains_dates_and_cumulative_path(self):
        _, window = market_adjusted_event_study(self.prices, "BET", "2026-01-06T14:00:00Z", "2026-01-31", 1, 1)
        self.assertTrue({"date", "relative_day", "instrument_return", "benchmark_return", "abnormal_return", "cumulative_abnormal_return"}.issubset(window.columns))
        self.assertAlmostEqual(window.iloc[-1].cumulative_abnormal_return, window.abnormal_return.sum())


if __name__ == "__main__":
    unittest.main()
