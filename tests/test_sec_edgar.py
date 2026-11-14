"""SEC EDGAR tests with a hand-made company-facts response (no network, no SEC_USER_AGENT needed)."""
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import sec_edgar  # noqa: E402


def fact(val, end, filed, start=None, form="10-K"):
    item = {"val": val, "end": end, "filed": filed, "form": form, "fp": "FY", "accn": f"0000-{filed}"}
    if start:
        item["start"] = start
    return item


FACTS = {"facts": {"us-gaap": {
    "Revenues": {"units": {"USD": [
        fact(1000, "2024-12-31", "2025-02-20", "2024-01-01"),
        fact(1200, "2025-12-31", "2026-02-18", "2025-01-01"),
        fact(300, "2025-12-31", "2026-02-18", "2025-10-01"),          # a quarter inside a 10-K: ignored
    ]}},
    "NetIncomeLoss": {"units": {"USD": [
        fact(100, "2024-12-31", "2025-02-20", "2024-01-01"),
        fact(90, "2024-12-31", "2026-02-18", "2024-01-01"),           # restated a year later
        fact(150, "2025-12-31", "2026-02-18", "2025-01-01"),
    ]}},
    "AssetsCurrent": {"units": {"USD": [fact(600, "2025-12-31", "2026-02-18")]}},
    "LiabilitiesCurrent": {"units": {"USD": [fact(300, "2025-12-31", "2026-02-18")]}},
    "LongTermDebt": {"units": {"USD": [fact(400, "2025-12-31", "2026-02-18")]}},
    "StockholdersEquity": {"units": {"USD": [fact(800, "2025-12-31", "2026-02-18")]}},
}}}
TICKERS = {"0": {"cik_str": 1234, "ticker": "ALP", "title": "ALPHA INDUSTRIES INC"}}


def fake_get(url, cache_name):
    return TICKERS if cache_name == "company_tickers.json" else FACTS


class SecEdgarTests(unittest.TestCase):
    def test_nothing_is_requested_without_a_declared_user_agent(self):
        with mock.patch.dict(os.environ, {"SEC_USER_AGENT": ""}):
            with self.assertRaises(sec_edgar.NotConfigured):
                sec_edgar.user_agent()
        with mock.patch.dict(os.environ, {"SEC_USER_AGENT": "Jane Doe jane@example.com"}):
            self.assertEqual(sec_edgar.user_agent(), "Jane Doe jane@example.com")

    def test_point_in_time_never_uses_later_restatements(self):
        frame = sec_edgar.annual_facts(FACTS)
        early = sec_edgar.as_of(frame, "2025-06-30")
        late = sec_edgar.as_of(frame, "2026-06-30")
        income = lambda known: known[(known.metric == "net_income") & (known.period_end == "2024-12-31")].value.iloc[0]  # noqa: E731
        self.assertEqual(income(early), 100)   # as originally reported
        self.assertEqual(income(late), 90)     # after the restatement was filed
        self.assertNotIn(300, set(frame[frame.metric == "revenue"].value))  # quarterly value excluded

    def test_company_summary_and_ratios(self):
        with mock.patch.object(sec_edgar, "_get_json", side_effect=fake_get):
            summary = sec_edgar.company("alp", "2026-06-30")
        self.assertEqual(summary["name"], "Alpha Industries Inc")
        self.assertEqual(summary["latest_period"], "2025-12-31")
        self.assertAlmostEqual(summary["ratios"]["net_margin"], 150 / 1200)
        self.assertAlmostEqual(summary["ratios"]["current_ratio"], 2.0)
        self.assertAlmostEqual(summary["ratios"]["debt_to_equity"], 0.5)
        self.assertEqual(summary["restatements"], 1)
        with mock.patch.object(sec_edgar, "_get_json", side_effect=fake_get):
            with self.assertRaises(ValueError):
                sec_edgar.company("NOPE", "2026-06-30")


if __name__ == "__main__":
    unittest.main()
