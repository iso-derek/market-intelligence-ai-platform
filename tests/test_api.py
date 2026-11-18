"""Contract tests for the JSON API behind the Market Signal web app.

The evidence database and saved runs go to a temporary folder; nothing touches
data/runtime or runs/, and no network fetch is made.
"""
import os
import tempfile
import unittest
from pathlib import Path

_TMP = tempfile.TemporaryDirectory()
os.environ["MARKET_INTELLIGENCE_DB"] = str(Path(_TMP.name) / "evidence.db")
os.environ["MARKET_INTELLIGENCE_RUNS"] = str(Path(_TMP.name) / "runs")

from fastapi.testclient import TestClient  # noqa: E402

from api.main import app  # noqa: E402


class MarketSignalApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        _TMP.cleanup()

    def get(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_demo_news_counts_only_real_risk_flags(self):
        news = self.get("/api/news")
        self.assertTrue(news["synthetic"])
        flagged = sum(1 for item in self.get("/api/news?limit=500")["headlines"] if item["risk"])
        self.assertEqual(news["kpis"]["risk_flagged"], flagged)
        self.assertTrue(all("none" not in [flag.lower() for flag in item["risk"]] for item in news["headlines"]))

    def test_demo_headlines_are_never_cited_but_uploads_are(self):
        self.assertTrue(self.client.post("/api/news/brief", json={"query": "interest rates"}).json()["abstained"])
        csv = ("headline,published_at,url,source\n"
               "Alpha Industries raises guidance on interest rates,2026-01-10T10:00:00Z,https://example.com/a,Example Wire\n")
        upload = self.client.post("/api/news/upload", json={"csv": csv})
        self.assertEqual(upload.status_code, 200, upload.text)
        brief = self.client.post("/api/news/brief", json={"source": upload.json()["source"], "query": "interest rates"}).json()
        self.assertFalse(brief["abstained"])
        self.assertEqual(brief["claims"][0]["url"], "https://example.com/a")

    def test_markets_respect_the_historical_view(self):
        before = self.get("/api/markets?view=before-revisions")
        after = self.get("/api/markets?view=revised")
        cpi = lambda data: next(item["value"] for item in data["macro"]["latest"] if item["id"] == "CPI_YOY")  # noqa: E731
        self.assertEqual((cpi(before), cpi(after)), (2.9, 3.0))
        self.assertEqual(self.client.get("/api/markets?view=tomorrow").status_code, 400)
        self.assertEqual(self.get("/api/markets/event")["peers"], 2)

    def test_watchlist_neutral_stress_changes_nothing(self):
        data = self.get("/api/watchlist?tickers=ALP,BET")
        self.assertEqual([row["ticker"] for row in data["snapshot"]], ["ALP", "BET"])
        neutral = self.get("/api/watchlist/stress?tickers=ALP&revenue=0&margin_bps=0&assets=0&liabilities=0&debt=0&equity=0")
        self.assertAlmostEqual(neutral["rows"][0]["change"], 0.0, places=9)

    def test_filings_answer_with_citation_or_abstain(self):
        answer = self.get("/api/filings/answer?q=What amounts did Alpha's warranty correction change net income from and to?")
        self.assertEqual(answer["status"], "answered")
        self.assertEqual(answer["citations"][0]["page"], 3)
        early = self.get("/api/filings?view=beta-only")
        self.assertEqual([doc["company"] for doc in early["documents"]], ["Beta Retail"])

    def test_workflow_runs_save_once_and_compare(self):
        workflow = self.get("/api/workflow?company=ALP")
        self.assertEqual([step["role"] for step in workflow["trace"]][:3], ["Company", "Macro", "News"])
        self.assertTrue(all("_" not in claim["label"] for claim in workflow["report"]["claims"]))
        first = self.client.post("/api/workflow/runs", json={"company": "ALP"}).json()
        repeat = self.client.post("/api/workflow/runs", json={"company": "ALP"}).json()
        self.assertTrue(first["created"])
        self.assertFalse(repeat["created"])
        self.client.post("/api/workflow/runs", json={"company": "ALP", "view": "before-revisions"})
        runs = self.get("/api/workflow/runs")["runs"]
        self.assertEqual(len(runs), 2)
        comparison = self.get(f"/api/workflow/compare?base={runs[1]['id']}&target={runs[0]['id']}")
        self.assertTrue(comparison["rows"])

    def test_graph_and_operations(self):
        self.assertLess(len(self.get("/api/graph?view=feb")["edges"]), len(self.get("/api/graph?view=mar")["edges"]))
        self.assertIn("health", self.get("/api/operations"))


if __name__ == "__main__":
    unittest.main()
