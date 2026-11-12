"""Deterministic research-report reconciliation and immutable export."""
from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
import zipfile

import pandas as pd


def _canonical_hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _decimal(value: object) -> Decimal:
    try:
        return Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"non-numeric report value: {value}") from exc


def build_reconciled_report(
    artifact: dict[str, object], evidence_catalog: dict[str, dict[str, object]]
) -> dict[str, object]:
    """Create unique numeric claims and verify every value against cited evidence."""
    request = artifact.get("request", {})
    cutoff = pd.Timestamp(request.get("as_of"))
    cutoff = cutoff.tz_localize("UTC") if cutoff.tzinfo is None else cutoff.tz_convert("UTC")
    seen: set[tuple[str, str, str, str]] = set()
    claims: list[dict[str, object]] = []
    reconciliation: list[dict[str, object]] = []
    for step in artifact.get("trace", []):
        for fact in step.get("facts", []):
            evidence_ids = list(fact.get("evidence_ids", []))
            if not evidence_ids:
                raise ValueError("report facts require claim-level citations")
            fingerprint = (
                str(fact["fact_key"]), str(fact["value"]), str(fact["unit"]),
                "|".join(sorted(evidence_ids)),
            )
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            citations = []
            for evidence_id in evidence_ids:
                if evidence_id not in evidence_catalog:
                    raise ValueError(f"unknown evidence ID: {evidence_id}")
                source = evidence_catalog[evidence_id]
                available_at = pd.Timestamp(source["available_at"])
                available_at = available_at.tz_localize("UTC") if available_at.tzinfo is None else available_at.tz_convert("UTC")
                if available_at > cutoff:
                    raise ValueError(f"future evidence is ineligible: {evidence_id}")
                value_ok = _decimal(fact["value"]) == _decimal(source["value"])
                unit_ok = str(fact["unit"]) == str(source["unit"])
                citations.append({
                    "evidence_id": evidence_id,
                    "uri": source["uri"],
                    "available_at": available_at.isoformat(),
                })
                reconciliation.append({
                    "fact_key": fact["fact_key"], "evidence_id": evidence_id,
                    "report_value": fact["value"], "source_value": source["value"],
                    "report_unit": fact["unit"], "source_unit": source["unit"],
                    "value_match": value_ok, "unit_match": unit_ok,
                })
                if not value_ok or not unit_ok:
                    raise ValueError(f"report value does not reconcile: {evidence_id}")
            claim_id = f"claim-{len(claims) + 1:03d}"
            claims.append({
                "claim_id": claim_id,
                "statement": f"{fact['fact_key'].replace('_', ' ').title()}: {fact['value']} {fact['unit']}",
                "fact_key": fact["fact_key"], "value": fact["value"], "unit": fact["unit"],
                "citations": citations,
            })
    if not claims:
        raise ValueError("report requires at least one reconciled claim")
    report = {
        "title": f"Evidence-backed research report — {request.get('company', 'Unknown')}",
        "question": request.get("question", ""), "as_of": cutoff.isoformat(),
        "workflow_artifact_sha256": artifact.get("artifact_sha256", ""),
        "status": "reconciled", "claims": claims, "reconciliation": reconciliation,
        "limitations": [
            "Fixture values are educational and not live market data.",
            "Citations and numeric equality do not establish investment significance or causality.",
            "Missing non-synthetic news evidence remains visible in the workflow trace.",
        ],
    }
    report["report_sha256"] = _canonical_hash(report)
    return report


def report_markdown(report: dict[str, object]) -> str:
    lines = [f"# {report['title']}", "", f"**As of:** {report['as_of']}", "", str(report["question"]), "", "## Reconciled claims", ""]
    for claim in report["claims"]:
        references = ", ".join(citation["evidence_id"] for citation in claim["citations"])
        lines.append(f"- **{claim['claim_id']}** — {claim['statement']}  ")
        lines.append(f"  Evidence: `{references}`")
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    lines.extend(["", f"Report SHA-256: `{report['report_sha256']}`", ""])
    return "\n".join(lines)


def export_report_bundle(report: dict[str, object]) -> bytes:
    files: dict[str, bytes] = {
        "report.json": json.dumps(report, indent=2, default=str).encode("utf-8"),
        "report.md": report_markdown(report).encode("utf-8"),
    }
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=list(report["reconciliation"][0]))
    writer.writeheader()
    writer.writerows(report["reconciliation"])
    files["reconciliation.csv"] = output.getvalue().encode("utf-8")
    manifest = {
        "report_sha256": report["report_sha256"],
        "files": {name: hashlib.sha256(content).hexdigest() for name, content in files.items()},
    }
    files["manifest.json"] = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, files[name])
    return buffer.getvalue()
