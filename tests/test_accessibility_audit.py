import tempfile
import unittest
from pathlib import Path

from src.accessibility_audit import audit_streamlit_file, audit_streamlit_project


ROOT = Path(__file__).resolve().parents[1]


class AccessibilityAuditTests(unittest.TestCase):
    def test_current_streamlit_surfaces_pass_static_audit(self):
        report = audit_streamlit_project(ROOT)
        self.assertTrue(report["passed"], report["findings"])
        self.assertGreaterEqual(report["files_scanned"], 5)

    def test_missing_alt_and_deprecated_width_are_detected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.py"
            path.write_text("import streamlit as st\nst.dataframe([], use_container_width=True)\n", encoding="utf-8")
            rules = {item["rule"] for item in audit_streamlit_file(path)}
            self.assertEqual(rules, {"missing-alt", "deprecated-width"})

    def test_empty_widget_label_and_unsafe_html_are_detected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.py"
            path.write_text("import streamlit as st\nst.text_input('')\nst.markdown('x', unsafe_allow_html=True)\n", encoding="utf-8")
            rules = {item["rule"] for item in audit_streamlit_file(path)}
            self.assertEqual(rules, {"empty-label", "unsafe-html"})

    def test_walkthrough_names_every_workspace(self):
        text = (ROOT / "docs/USER_WALKTHROUGH.md").read_text(encoding="utf-8")
        for workspace in ("News evidence", "Market, macro & fundamentals", "Filings corpus", "Research workflow", "Evidence graph & operations"):
            self.assertIn(workspace, text)


if __name__ == "__main__":
    unittest.main()
