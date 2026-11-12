import unittest
from pathlib import Path

import pandas as pd

from src.filings import load_filings_corpus
from src.retrieval import (
    evaluate_retriever,
    file_sha256,
    load_relevance_cases,
    rank_passages,
    rank_passages_as_of,
)


ROOT = Path(__file__).resolve().parents[1]


class FilingRetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, cls.passages = load_filings_corpus(ROOT / "data" / "filings")
        cls.cases_path = ROOT / "data" / "evaluation" / "filings_relevance_cases.csv"
        cls.cases = load_relevance_cases(cls.cases_path)

    def test_lexical_ranking_returns_provenance_and_stable_order(self):
        first = rank_passages(self.passages, "warranty provision net income correction", "lexical", 3)
        second = rank_passages(self.passages, "warranty provision net income correction", "lexical", 3)
        self.assertEqual(first.passage_id.tolist(), second.passage_id.tolist())
        self.assertEqual(first.iloc[0].passage_id, "filing-alp-2025:p3:s1")
        self.assertTrue({"document_id", "page", "section", "text_sha256", "score", "rank"}.issubset(first.columns))

    def test_dense_lsa_ranking_is_deterministic(self):
        first = rank_passages(self.passages, "subscription revenue implementation services", "dense_lsa", 5)
        second = rank_passages(self.passages, "subscription revenue implementation services", "dense_lsa", 5)
        self.assertEqual(first.passage_id.tolist(), second.passage_id.tolist())
        self.assertTrue((first.score.round(12) == second.score.round(12)).all())
        self.assertEqual(first.iloc[0].passage_id, "filing-gam-2025:p3:s1")

    def test_cutoff_is_applied_before_model_fit_and_ranking(self):
        ranked = rank_passages_as_of(
            self.passages, "Alpha warranty provision", "2026-02-01T23:59:59Z", "lexical", 18
        )
        self.assertNotIn("filing-alp-2025", set(ranked.document_id))
        self.assertEqual(set(ranked.ticker), {"BET", "GAM"})

    def test_frozen_cases_have_identity_and_review_markers(self):
        self.assertEqual(len(self.cases), 8)
        self.assertEqual(set(self.cases.review_status), {"fixture_author_reviewed"})
        self.assertEqual(set(self.cases.split), {"frozen_diagnostic"})
        self.assertEqual(len(file_sha256(self.cases_path)), 64)

    def test_both_methods_export_bounded_metrics_and_case_details(self):
        for method in ("lexical", "dense_lsa"):
            summary, details = evaluate_retriever(self.passages, self.cases, method, top_k=3)
            self.assertEqual(summary["case_count"], 8)
            for metric in ("mean_recall_at_3", "mean_reciprocal_rank", "mean_ndcg_at_3"):
                self.assertGreaterEqual(summary[metric], 0.0)
                self.assertLessEqual(summary[metric], 1.0)
            self.assertEqual(len(details), 8)
            self.assertTrue(details.retrieved_passage_ids.str.len().gt(0).all())

    def test_evaluation_rejects_labels_that_leak_past_cutoff(self):
        cases = self.cases.iloc[[0]].copy()
        cases.loc[:, "cutoff"] = pd.Timestamp("2026-02-01T23:59:59Z")
        with self.assertRaisesRegex(ValueError, "unavailable at its cutoff"):
            evaluate_retriever(self.passages, cases, "lexical", top_k=3)

    def test_invalid_method_query_and_k_fail_closed(self):
        with self.assertRaises(ValueError):
            rank_passages(self.passages, "query", "unknown", 3)
        with self.assertRaises(ValueError):
            rank_passages(self.passages, " ", "lexical", 3)
        with self.assertRaises(ValueError):
            rank_passages(self.passages, "query", "lexical", 0)


if __name__ == "__main__":
    unittest.main()
