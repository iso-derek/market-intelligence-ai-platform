import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.evidence_graph import evidence_paths, graph_as_of, load_evidence_graph, operations_report


ROOT = Path(__file__).resolve().parents[1]


class EvidenceGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nodes_path = ROOT / "data" / "fixtures" / "evidence_graph_nodes.csv"
        cls.edges_path = ROOT / "data" / "fixtures" / "evidence_graph_edges.csv"
        cls.nodes, cls.edges, cls.graph_hash = load_evidence_graph(cls.nodes_path, cls.edges_path)

    def test_graph_has_unique_non_dangling_hash_identified_records(self):
        self.assertEqual(len(self.nodes), 6)
        self.assertEqual(len(self.edges), 5)
        self.assertEqual(len(self.graph_hash), 64)

    def test_point_in_time_graph_excludes_later_filing_chain(self):
        nodes, edges = graph_as_of(self.nodes, self.edges, "2026-02-01")
        self.assertEqual(set(nodes.node_id), {"company:ALP", "instrument:ALP"})
        self.assertTrue(edges.empty)

    def test_paths_preserve_non_causal_relationship_language(self):
        paths = evidence_paths(self.edges, "company:ALP", 4)
        self.assertIn("supports", " ".join(paths.relationships))
        self.assertNotIn("caused", " ".join(paths.relationships))
        self.assertTrue(paths.hops.le(4).all())

    def test_cycles_are_not_revisited(self):
        cyclic = pd.concat([self.edges, pd.DataFrame([{"edge_id": "cycle", "source_id": "instrument:ALP", "target_id": "company:ALP", "relationship": "linked_to", "evidence_id": "instrument:ALP", "available_at": pd.Timestamp("2026-02-20T20:05:00Z")}])], ignore_index=True)
        paths = evidence_paths(cyclic, "company:ALP", 8)
        self.assertFalse(paths.path.str.contains("company:ALP.*company:ALP").any())

    def test_dangling_reference_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "data" / "runtime") as folder:
            broken = self.edges.copy()
            broken.loc[0, "target_id"] = "missing"
            edge_path = Path(folder) / "edges.csv"
            broken.to_csv(edge_path, index=False)
            with self.assertRaisesRegex(ValueError, "dangling"):
                load_evidence_graph(self.nodes_path, edge_path)

    def test_operations_report_is_honest_about_local_demo(self):
        report = operations_report(ROOT, self.graph_hash)
        self.assertTrue(report["required_files_ok"])
        self.assertEqual(report["deployment_status"], "verified_local_demo_not_hosted")


if __name__ == "__main__":
    unittest.main()
