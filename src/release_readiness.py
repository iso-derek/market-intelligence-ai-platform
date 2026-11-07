"""Deterministic release-candidate checks that never deploy or approve a release."""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
from typing import Iterable


REQUIRED_FILES = (
    "README.md", "requirements.txt", "requirements-tested.txt", "app.py", "launch.py",
    ".github/workflows/tests.yml", "docs/ROADMAP.md", "docs/DEVELOPMENT_STATUS.md",
    "docs/USER_WALKTHROUGH.md", "docs/BACKUP_AND_RECOVERY.md", "docs/DEPLOYMENT_PLAN.md",
)
FORBIDDEN_TRACKED_NAMES = {".env", "secrets.toml", "id_rsa", "id_ed25519"}
SECRET_PATTERNS = {
    "aws-access-key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "openai-key": re.compile(r"sk-(?:proj-)?[A-Za-z0-9_-]{20,}"),
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "assigned-secret": re.compile(r"(?i)(?:api[_-]?key|secret[_-]?key|password)\s*=\s*['\"][^'\"\r\n]{8,}['\"]"),
}


def scan_tracked_secrets(root: str | Path, tracked_files: Iterable[str]) -> list[dict[str, str]]:
    root = Path(root)
    findings: list[dict[str, str]] = []
    for relative in sorted(set(str(item).replace("\\", "/") for item in tracked_files)):
        path = root / relative
        if path.name.casefold() in FORBIDDEN_TRACKED_NAMES:
            findings.append({"file": relative, "rule": "forbidden-secret-filename"})
        if not path.is_file() or path.stat().st_size > 1_000_000:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for name, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                findings.append({"file": relative, "rule": name})
    return findings


def validate_release_candidate(
    root: str | Path, tracked_files: Iterable[str], python_version: tuple[int, int]
) -> dict[str, object]:
    root = Path(root)
    missing = [item for item in REQUIRED_FILES if not (root / item).is_file()]
    secret_findings = scan_tracked_secrets(root, tracked_files)
    readme = (root / "README.md").read_text(encoding="utf-8") if (root / "README.md").is_file() else ""
    boundary_checks = {
        "local_demo_boundary": "No hosted deployment is claimed." in readme,
        "no_investment_advice": "does not provide investment advice" in readme,
        "owner_approval_required": "Deployment requires separate approval." in readme,
    }
    checks = {
        "supported_python": python_version in {(3, 12), (3, 13)},
        "required_files": not missing,
        "tracked_secrets": not secret_findings,
        "deployment_boundaries": all(boundary_checks.values()),
    }
    payload = {
        "status": "ready_for_owner_review" if all(checks.values()) else "not_ready",
        "checks": checks, "missing_files": missing, "secret_findings": secret_findings,
        "boundary_checks": boundary_checks,
        "limitations": "This check does not merge, deploy, approve a release, test external providers, or replace the CI matrix.",
    }
    payload["audit_sha256"] = hashlib.sha256(
        repr((checks, missing, secret_findings, boundary_checks)).encode("utf-8")
    ).hexdigest()
    return payload
