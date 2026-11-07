"""Print the local release-candidate audit and return nonzero when it fails."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from release_readiness import validate_release_candidate


def main() -> int:
    tracked = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", "ls-files"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    report = validate_release_candidate(ROOT, tracked, sys.version_info[:2])
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "ready_for_owner_review" else 1


if __name__ == "__main__":
    raise SystemExit(main())
