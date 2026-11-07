import tempfile
import unittest
from pathlib import Path

from src.release_readiness import scan_tracked_secrets, validate_release_candidate


ROOT = Path(__file__).resolve().parents[1]


class ReleaseReadinessTests(unittest.TestCase):
    def test_current_tracked_tree_is_ready_for_owner_review(self):
        import subprocess
        tracked = subprocess.run(
            ["git", "-c", f"safe.directory={ROOT.as_posix()}", "ls-files"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.splitlines()
        report = validate_release_candidate(ROOT, tracked, (3, 12))
        self.assertEqual(report["status"], "ready_for_owner_review", report)
        self.assertTrue(all(report["checks"].values()))

    def test_unsupported_python_fails(self):
        report = validate_release_candidate(ROOT, [], (3, 11))
        self.assertFalse(report["checks"]["supported_python"])
        self.assertEqual(report["status"], "not_ready")

    def test_secret_patterns_and_names_are_detected_without_echoing_values(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "data/runtime") as folder:
            root = Path(folder)
            secret_text = "SERVICE_" + "PASSWORD=" + "'super-secret-value'\n"
            (root / ".env").write_text(secret_text, encoding="utf-8")
            findings = scan_tracked_secrets(root, [".env"])
            self.assertEqual({item["rule"] for item in findings}, {"forbidden-secret-filename", "assigned-secret"})
            self.assertNotIn("super-secret-value", repr(findings))

    def test_missing_required_file_fails(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "data/runtime") as folder:
            root = Path(folder)
            (root / "README.md").write_text("No hosted deployment is claimed. does not provide investment advice Deployment requires separate approval.", encoding="utf-8")
            report = validate_release_candidate(root, ["README.md"], (3, 12))
            self.assertFalse(report["checks"]["required_files"])
            self.assertIn("app.py", report["missing_files"])

    def test_audit_hash_is_stable(self):
        first = validate_release_candidate(ROOT, [], (3, 12))
        second = validate_release_candidate(ROOT, [], (3, 12))
        self.assertEqual(first["audit_sha256"], second["audit_sha256"])


if __name__ == "__main__":
    unittest.main()
