"""Append-only local history for typed workflow and reconciled report artifacts."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import uuid

import pandas as pd


def _json_bytes(payload: object, *, pretty: bool = False) -> bytes:
    separators = None if pretty else (",", ":")
    indent = 2 if pretty else None
    return json.dumps(payload, sort_keys=True, separators=separators, indent=indent, default=str).encode("utf-8")


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _identity_payload(manifest: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": manifest["schema_version"],
        "run_kind": manifest["run_kind"],
        "research_as_of": manifest["research_as_of"],
        "company": manifest["company"],
        "question": manifest["question"],
        "status": manifest["status"],
        "artifacts": manifest["artifacts"],
        "workflow_artifact_sha256": manifest["workflow_artifact_sha256"],
        "report_sha256": manifest["report_sha256"],
    }


def _safe_artifact(folder: Path, relative: object) -> Path:
    value = Path(str(relative))
    if value.is_absolute() or ".." in value.parts:
        raise ValueError(f"unsafe run artifact path: {relative}")
    target = (folder / value).resolve()
    if folder.resolve() not in target.parents:
        raise ValueError(f"run artifact escapes its folder: {relative}")
    return target


def save_workflow_run(
    root: str | Path,
    artifact: dict[str, object],
    report: dict[str, object],
    recorded_at: object | None = None,
) -> tuple[Path, bool]:
    """Atomically persist a content-addressed workflow run without overwriting history."""
    request = artifact.get("request")
    if not isinstance(request, dict):
        raise ValueError("workflow artifact requires a request")
    for key in ("question", "as_of", "company"):
        if not str(request.get(key, "")).strip():
            raise ValueError(f"workflow request requires {key}")
    workflow_hash = str(artifact.get("artifact_sha256", ""))
    report_hash = str(report.get("report_sha256", ""))
    if len(workflow_hash) != 64 or len(report_hash) != 64:
        raise ValueError("workflow and report require 64-character SHA-256 identities")

    workflow_bytes = _json_bytes(artifact, pretty=True)
    report_bytes = _json_bytes(report, pretty=True)
    artifacts = [
        {"path": "workflow.json", "sha256": _sha256(workflow_bytes)},
        {"path": "report.json", "sha256": _sha256(report_bytes)},
    ]
    timestamp = pd.Timestamp(recorded_at or datetime.now(timezone.utc))
    timestamp = timestamp.tz_localize("UTC") if timestamp.tzinfo is None else timestamp.tz_convert("UTC")
    manifest: dict[str, object] = {
        "schema_version": 2,
        "run_kind": "typed_workflow",
        "research_as_of": pd.Timestamp(request["as_of"]).isoformat(),
        "recorded_at": timestamp.isoformat(),
        "company": str(request["company"]),
        "question": str(request["question"]),
        "status": str(artifact.get("status", "unknown")),
        "artifacts": artifacts,
        "workflow_artifact_sha256": workflow_hash,
        "report_sha256": report_hash,
        "limitations": (
            "Local single-process content-addressed history. A stored run is reproducible evidence of inputs and "
            "outputs, not proof of research validity or investment significance."
        ),
    }
    run_sha = _sha256(_json_bytes(_identity_payload(manifest)))
    run_id = f"workflow-{run_sha[:16]}"
    manifest["run_id"] = run_id
    manifest["run_sha256"] = run_sha

    root_path = Path(root)
    root_path.mkdir(parents=True, exist_ok=True)
    destination = root_path / run_id
    if destination.exists():
        existing = load_workflow_run(destination)
        if existing["manifest"]["run_sha256"] != run_sha:
            raise ValueError(f"run folder collision: {run_id}")
        return destination, False

    partial = root_path / f".{run_id}.partial-{uuid.uuid4().hex}"
    partial.mkdir(parents=False, exist_ok=False)
    try:
        (partial / "workflow.json").write_bytes(workflow_bytes)
        (partial / "report.json").write_bytes(report_bytes)
        (partial / "manifest.json").write_bytes(_json_bytes(manifest, pretty=True))
        os.rename(partial, destination)
    except Exception:
        if partial.exists():
            shutil.rmtree(partial)
        raise
    return destination, True


def load_workflow_run(folder: str | Path) -> dict[str, object]:
    """Load and fully verify one stored workflow run."""
    run_folder = Path(folder)
    manifest_path = run_folder / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError(f"run manifest is missing: {run_folder.name}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(f"run manifest is invalid: {run_folder.name}") from exc
    if manifest.get("schema_version") != 2 or manifest.get("run_kind") != "typed_workflow":
        raise ValueError(f"unsupported workflow-run schema: {run_folder.name}")
    if manifest.get("run_id") != run_folder.name:
        raise ValueError(f"run folder does not match manifest identity: {run_folder.name}")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or {item.get("path") for item in artifacts} != {"workflow.json", "report.json"}:
        raise ValueError(f"workflow run has an invalid artifact set: {run_folder.name}")
    payloads: dict[str, object] = {}
    for item in artifacts:
        path = _safe_artifact(run_folder, item["path"])
        if not path.is_file():
            raise ValueError(f"run artifact is missing: {item['path']}")
        content = path.read_bytes()
        if _sha256(content) != item.get("sha256"):
            raise ValueError(f"run artifact hash mismatch: {item['path']}")
        try:
            payloads[path.stem] = json.loads(content)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError(f"run artifact is invalid JSON: {item['path']}") from exc
    expected = _sha256(_json_bytes(_identity_payload(manifest)))
    if manifest.get("run_sha256") != expected or manifest.get("run_id") != f"workflow-{expected[:16]}":
        raise ValueError(f"run identity mismatch: {run_folder.name}")
    if payloads["workflow"].get("artifact_sha256") != manifest.get("workflow_artifact_sha256"):
        raise ValueError("workflow identity does not match its manifest")
    if payloads["report"].get("report_sha256") != manifest.get("report_sha256"):
        raise ValueError("report identity does not match its manifest")
    return {"folder": run_folder, "manifest": manifest, **payloads}


def workflow_run_history(root: str | Path) -> pd.DataFrame:
    """Return verified typed-workflow history; legacy CLI run folders are ignored."""
    root_path = Path(root)
    columns = [
        "run_id",
        "recorded_at",
        "research_as_of",
        "company",
        "status",
        "workflow_artifact_sha256",
        "report_sha256",
        "run_sha256",
        "folder",
    ]
    if not root_path.exists():
        return pd.DataFrame(columns=columns)
    rows: list[dict[str, object]] = []
    for folder in sorted(root_path.iterdir()):
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        manifest_path = folder / "manifest.json"
        if not manifest_path.is_file():
            continue
        try:
            header = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError(f"run manifest is invalid: {folder.name}") from exc
        if header.get("run_kind") != "typed_workflow":
            continue
        loaded = load_workflow_run(folder)
        manifest = loaded["manifest"]
        rows.append({**{column: manifest.get(column) for column in columns if column != "folder"}, "folder": str(folder)})
    if not rows:
        return pd.DataFrame(columns=columns)
    output = pd.DataFrame(rows, columns=columns)
    output["recorded_at"] = pd.to_datetime(output["recorded_at"], utc=True)
    output["research_as_of"] = pd.to_datetime(output["research_as_of"], utc=True)
    return output.sort_values(["recorded_at", "run_id"], ascending=[False, True]).reset_index(drop=True)


def _run_metrics(loaded: dict[str, object]) -> dict[str, object]:
    workflow = loaded["workflow"]
    report = loaded["report"]
    trace = workflow.get("trace", [])
    return {
        "company": workflow["request"]["company"],
        "research_as_of": pd.Timestamp(workflow["request"]["as_of"]),
        "status": workflow.get("status", "unknown"),
        "steps_used": workflow.get("budget", {}).get("steps_used", 0),
        "missing_roles": sum(row.get("status") == "missing" for row in trace),
        "conflicts": sum(row.get("status") == "conflict" for row in trace),
        "facts": sum(len(row.get("facts", [])) for row in trace),
        "citations": sum(len(row.get("citations", [])) for row in trace),
        "reconciled_claims": len(report.get("claims", [])),
        "workflow_artifact_sha256": workflow.get("artifact_sha256", ""),
        "report_sha256": report.get("report_sha256", ""),
    }


def compare_workflow_runs(base_folder: str | Path, target_folder: str | Path) -> dict[str, object]:
    """Compare verified run outputs while keeping historical cutoffs explicit."""
    base = _run_metrics(load_workflow_run(base_folder))
    target = _run_metrics(load_workflow_run(target_folder))
    base_cutoff = pd.Timestamp(base["research_as_of"])
    target_cutoff = pd.Timestamp(target["research_as_of"])
    relation = "same_cutoff" if target_cutoff == base_cutoff else "target_later" if target_cutoff > base_cutoff else "target_earlier"
    rows: list[dict[str, object]] = []
    for metric in base:
        base_value = base[metric]
        target_value = target[metric]
        if isinstance(base_value, int) and isinstance(target_value, int):
            change: object = target_value - base_value
        else:
            change = "unchanged" if str(base_value) == str(target_value) else "changed"
        rows.append({"metric": metric, "base": base_value, "target": target_value, "change": change})
    return {
        "cutoff_relation": relation,
        "same_company": base["company"] == target["company"],
        "metrics": pd.DataFrame(rows),
        "limitations": (
            "Differences describe two stored outputs. They do not establish causality, improvement, forecast accuracy, "
            "or investment significance."
        ),
    }
