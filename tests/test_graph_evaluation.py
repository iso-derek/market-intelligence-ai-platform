import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.evidence_graph import load_evidence_graph
from src.graph_evaluation import evaluate_graph_value, load_graph_value_cases


ROOT = Path(__file__).resolve().parents[1]


class GraphValueEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nodes, cls.edges, _ = load_evidence_graph(
            ROOT / "data/fixtures/evidence_graph_nodes.csv",
            ROOT / "data/fixtures/evidence_graph_edges.csv",
        )
        cls.cases, cls.case_hash = load_graph_value_cases(
            ROOT / "data/evaluation/graph_value_cases.csv"
        )

    def test_frozen_cases_have_stable_identity(self):
        self.assertEqual(len(self.cases), 5)
        self.assertEqual(len(self.case_hash), 64)

    def test_graph_and_table_are_exact_on_frozen_cases(self):
        report = evaluate_graph_value(self.nodes, self.edges, self.cases, self.case_hash)
        self.assertEqual(report["graph_exact_rate"], 1.0)
        self.assertEqual(report["table_exact_rate"], 1.0)
        self.assertEqual(report["method_parity_rate"], 1.0)

    def test_historical_case_excludes_future_chain(self):
        report = evaluate_graph_value(self.nodes, self.edges, self.cases, self.case_hash)
        result = report["results"].set_index("case_id").loc["graph-005"]
        self.assertFalse(result.graph_found)
        self.assertFalse(result.table_found)

    def test_adjacency_reduces_repeated_row_inspection(self):
        report = evaluate_graph_value(self.nodes, self.edges, self.cases, self.case_hash)
        self.assertLess(report["graph_edges_inspected"], report["table_rows_inspected"])
        self.assertGreater(report["inspection_reduction"], 0)

    def test_malformed_cases_are_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "data/runtime") as folder:
            path = Path(folder) / "cases.csv"
            pd.DataFrame({"case_id": ["x"]}).to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, "schema"):
                load_graph_value_cases(path)


if __name__ == "__main__":
    unittest.main()
