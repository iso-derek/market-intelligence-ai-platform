import io
import json
import unittest
import zipfile

from src.research_report import build_reconciled_report, export_report_bundle
from src.workflows import WorkflowRequest, make_demo_tools, run_workflow


FACTS = [{"fact_key": "revenue", "value": 1000, "unit": "USD million", "evidence_ids": ["filing:p1"]}]
CATALOG = {"filing:p1": {"value": 1000, "unit": "USD million", "uri": "repo://filing#p1", "available_at": "2026-02-20T20:05:00Z"}}


def artifact():
    request = WorkflowRequest("What is revenue?", "2026-03-01T23:59:59Z", "ALP")
    return run_workflow(request, make_demo_tools(FACTS, [], []))


class ReconciledResearchReportTests(unittest.TestCase):
    def test_report_has_unique_claim_level_citations_and_hash(self):
        report = build_reconciled_report(artifact(), CATALOG)
        self.assertEqual(report["status"], "reconciled")
        self.assertEqual(len(report["claims"]), 1)
        self.assertEqual(report["claims"][0]["citations"][0]["evidence_id"], "filing:p1")
        self.assertEqual(len(report["report_sha256"]), 64)

    def test_numeric_or_unit_mismatch_fails_closed(self):
        bad = {"filing:p1": {**CATALOG["filing:p1"], "value": 999}}
        with self.assertRaisesRegex(ValueError, "does not reconcile"):
            build_reconciled_report(artifact(), bad)

    def test_unknown_and_future_evidence_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "unknown evidence"):
            build_reconciled_report(artifact(), {})
        future = {"filing:p1": {**CATALOG["filing:p1"], "available_at": "2027-01-01T00:00:00Z"}}
        with self.assertRaisesRegex(ValueError, "future evidence"):
            build_reconciled_report(artifact(), future)

    def test_bundle_contains_report_reconciliation_and_hash_manifest(self):
        report = build_reconciled_report(artifact(), CATALOG)
        with zipfile.ZipFile(io.BytesIO(export_report_bundle(report))) as archive:
            self.assertEqual(set(archive.namelist()), {"manifest.json", "reconciliation.csv", "report.json", "report.md"})
            manifest = json.loads(archive.read("manifest.json"))
            self.assertEqual(manifest["report_sha256"], report["report_sha256"])
            self.assertEqual(json.loads(archive.read("report.json"))["status"], "reconciled")

    def test_bundle_is_byte_reproducible(self):
        report = build_reconciled_report(artifact(), CATALOG)
        self.assertEqual(export_report_bundle(report), export_report_bundle(report))


if __name__ == "__main__":
    unittest.main()
