"""D8.3 append-only research history and comparison tests."""
from pathlib import Path
import sys
import tempfile
import unittest

import pandas as pd
import pyarrow as pa

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "data" / "runtime"
sys.path.insert(0, str(ROOT / "src"))

from research_history import (  # noqa: E402
    comparison_display_frame,
    compare_workflow_runs,
    load_workflow_run,
    save_workflow_run,
    workflow_run_history,
)


def fixture_run(
    marker: str,
    *,
    company: str = "ALP",
    as_of: str = "2026-01-31T23:59:59Z",
    missing: int = 1,
) -> tuple[dict[str, object], dict[str, object]]:
    trace = [
        {"step": 1, "role": "Company", "status": "complete", "facts": [{"fact_key": "revenue"}], "citations": ["filing"]},
        {"step": 2, "role": "News", "status": "missing" if missing else "complete", "facts": [], "citations": []},
    ]
    artifact = {
        "request": {"question": f"Question {marker}", "as_of": as_of, "company": company},
        "status": "partial" if missing else "complete",
        "budget": {"steps_used": 2},
        "trace": trace,
        "artifact_sha256": marker * 64,
    }
    report = {
        "claims": [{"claim_id": "claim-001"}],
        "report_sha256": marker.upper() * 64,
    }
    return artifact, report


class ResearchHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        RUNTIME.mkdir(parents=True, exist_ok=True)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=RUNTIME)
        self.root = Path(self.temp.name) / "runs"

    def tearDown(self):
        self.temp.cleanup()

    def test_save_is_content_addressed_and_never_overwrites(self):
        artifact, report = fixture_run("a")
        first, created_first = save_workflow_run(self.root, artifact, report, "2026-03-01T10:00:00Z")
        second, created_second = save_workflow_run(self.root, artifact, report, "2026-03-02T10:00:00Z")
        self.assertTrue(created_first)
        self.assertFalse(created_second)
        self.assertEqual(first, second)
        self.assertEqual(len(list(self.root.iterdir())), 1)

    def test_different_artifacts_create_distinct_runs(self):
        first = save_workflow_run(self.root, *fixture_run("a"))[0]
        second = save_workflow_run(self.root, *fixture_run("b"))[0]
        self.assertNotEqual(first.name, second.name)
        self.assertEqual(len(list(self.root.iterdir())), 2)

    def test_history_is_verified_and_sorted_by_recorded_time(self):
        save_workflow_run(self.root, *fixture_run("a"), recorded_at="2026-03-01T10:00:00Z")
        save_workflow_run(self.root, *fixture_run("b"), recorded_at="2026-03-02T10:00:00Z")
        history = workflow_run_history(self.root)
        self.assertEqual(len(history), 2)
        self.assertEqual(history.iloc[0].recorded_at.isoformat(), "2026-03-02T10:00:00+00:00")
        self.assertEqual(set(history.research_as_of.dt.tz_convert("UTC").dt.date.astype(str)), {"2026-01-31"})

    def test_comparison_reports_cutoff_direction_and_metric_deltas(self):
        base = save_workflow_run(self.root, *fixture_run("a", missing=1))[0]
        target = save_workflow_run(
            self.root,
            *fixture_run("b", as_of="2026-03-01T23:59:59Z", missing=0),
        )[0]
        comparison = compare_workflow_runs(base, target)
        metrics = comparison["metrics"].set_index("metric")
        self.assertEqual(comparison["cutoff_relation"], "target_later")
        self.assertTrue(comparison["same_company"])
        self.assertEqual(metrics.loc["missing_roles", "change"], -1)
        self.assertEqual(metrics.loc["status", "change"], "changed")

    def test_comparison_display_frame_is_arrow_safe_and_iso_dated(self):
        metrics = pd.DataFrame(
            [
                {"metric": "research_as_of", "base": pd.Timestamp("2026-01-31T23:59:59Z"), "target": pd.Timestamp("2026-03-01T23:59:59Z"), "change": "changed"},
                {"metric": "steps_used", "base": 5, "target": 5, "change": 0},
            ]
        )
        display = comparison_display_frame(metrics)
        self.assertTrue(all(str(dtype) == "string" for dtype in display.dtypes))
        self.assertEqual(display.loc[0, "base"], "2026-01-31T23:59:59+00:00")
        self.assertEqual(display.loc[1, "change"], "0")
        self.assertEqual(pa.Table.from_pandas(display).num_rows, 2)

    def test_comparison_keeps_company_changes_explicit(self):
        base = save_workflow_run(self.root, *fixture_run("a", company="ALP"))[0]
        target = save_workflow_run(self.root, *fixture_run("b", company="BET"))[0]
        comparison = compare_workflow_runs(base, target)
        self.assertFalse(comparison["same_company"])
        self.assertEqual(comparison["cutoff_relation"], "same_cutoff")

    def test_artifact_tampering_is_rejected(self):
        folder = save_workflow_run(self.root, *fixture_run("a"))[0]
        (folder / "workflow.json").write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            load_workflow_run(folder)
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            workflow_run_history(self.root)

    def test_missing_identities_fail_closed(self):
        artifact, report = fixture_run("a")
        artifact["artifact_sha256"] = "short"
        with self.assertRaisesRegex(ValueError, "64-character"):
            save_workflow_run(self.root, artifact, report)

    def test_historical_workflow_grids_have_context_specific_keys(self):
        source = (ROOT / "src" / "workflow_dashboard.py").read_text(encoding="utf-8")
        self.assertIn('key=f"workflow_trace_{company}_{cutoff_label}"', source)
        self.assertIn('key=f"workflow_reconciliation_{company}_{cutoff_label}"', source)


if __name__ == "__main__":
    unittest.main()
