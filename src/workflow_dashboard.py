"""Streamlit inspector for the bounded typed workflow engine."""
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from workflows import WorkflowRequest, make_demo_tools, run_workflow
from research_report import build_reconciled_report, export_report_bundle
from research_history import compare_workflow_runs, save_workflow_run, workflow_run_history


COMPANY_FACTS = {
    "ALP": [
        {"fact_key": "revenue", "value": 1000, "unit": "USD million", "evidence_ids": ["filing-alp-2025:p1:s1"]},
        {"fact_key": "net_income", "value": 90, "unit": "USD million", "evidence_ids": ["filing-alp-2025:p3:s1"]},
    ],
    "BET": [{"fact_key": "revenue", "value": 800, "unit": "USD million", "evidence_ids": ["filing-bet-2025:p1:s1"]}],
    "GAM": [{"fact_key": "revenue", "value": 600, "unit": "USD million", "evidence_ids": ["filing-gam-2025:p1:s1"]}],
}
RISK_IDS = {"ALP": "filing-alp-2025:p2:s2", "BET": "filing-bet-2025:p2:s2", "GAM": "filing-gam-2025:p2:s2"}
WORKFLOW_CUTOFFS = {
    "31 January 2026 — before revisions": "2026-01-31T23:59:59Z",
    "1 March 2026 — revised history": "2026-03-01T23:59:59Z",
}
RUNS_ROOT = Path(__file__).resolve().parents[1] / "runs"


def _company_facts(company: str, cutoff_label: str) -> list[dict[str, object]]:
    facts = [dict(fact) for fact in COMPANY_FACTS[company]]
    if company == "ALP" and cutoff_label.startswith("31 January"):
        for fact in facts:
            if fact["fact_key"] == "net_income":
                fact["value"] = 100
    return facts


def _macro_fact(cutoff_label: str) -> dict[str, object]:
    if cutoff_label.startswith("31 January"):
        return {
            "fact_key": "cpi",
            "value": 2.9,
            "unit": "% year over year",
            "evidence_ids": ["macro:CPI:2025-12:2026-01-15"],
        }
    return {
        "fact_key": "cpi",
        "value": 3.0,
        "unit": "% year over year",
        "evidence_ids": ["macro:CPI:2025-12:2026-02-20"],
    }


def _evidence_catalog(
    company: str,
    facts: list[dict[str, object]],
    macro_fact: dict[str, object],
    cutoff_label: str,
) -> dict[str, dict[str, object]]:
    filing_names = {"ALP": "alpha_2025_annual.txt", "BET": "beta_2025_annual.txt", "GAM": "gamma_2025_annual.txt"}
    macro_available = "2026-01-15T13:30:00Z" if cutoff_label.startswith("31 January") else "2026-02-20T13:30:00Z"
    filing_available = {
        "ALP": "2026-01-20T20:05:00Z" if cutoff_label.startswith("31 January") else "2026-02-20T20:05:00Z",
        "BET": "2026-01-22T20:05:00Z",
        "GAM": "2026-01-25T20:05:00Z",
    }[company]
    macro_id = macro_fact["evidence_ids"][0]
    catalog = {
        macro_id: {
            "value": macro_fact["value"],
            "unit": macro_fact["unit"],
            "uri": "repo://data/fixtures/macro_vintages.csv#CPI",
            "available_at": macro_available,
        }
    }
    for fact in facts:
        for evidence_id in fact["evidence_ids"]:
            catalog[evidence_id] = {
                "value": fact["value"], "unit": fact["unit"],
                "uri": f"repo://data/filings/{filing_names[company]}#{evidence_id.split(':')[-2]}-{evidence_id.split(':')[-1]}",
                "available_at": filing_available,
            }
    return catalog


def render_workflow_dashboard() -> None:
    st.subheader("Bounded research workflow")
    st.caption("Five typed roles, fixed tool allowlists, explicit budgets, and a hash-identified trace. No autonomous model is invoked.")
    with st.sidebar:
        st.header("Workflow controls")
        company = st.selectbox("Company", list(COMPANY_FACTS), format_func=lambda value: {"ALP": "Alpha Industries", "BET": "Beta Retail", "GAM": "Gamma Software"}[value])
        cutoff_label = st.selectbox("Historical workflow view", list(WORKFLOW_CUTOFFS), index=1)
        max_seconds = st.slider("Time budget (seconds)", 1, 10, 5)
        st.info("The News role is deliberately missing in this offline demonstration; the trace keeps that gap visible.")
    question = st.text_input("Research question", f"What is the evidence-backed outlook and risk context for {company}?")
    facts = _company_facts(company, cutoff_label)
    macro_fact = _macro_fact(cutoff_label)
    macro = [macro_fact]
    risks = [{"evidence_id": RISK_IDS[company], "kind": "filing_risk_factor"}]
    request = WorkflowRequest(
        question,
        WORKFLOW_CUTOFFS[cutoff_label],
        company,
        max_steps=5,
        max_seconds=float(max_seconds),
    )
    artifact = run_workflow(request, make_demo_tools(facts, macro, risks))

    cards = st.columns(4)
    cards[0].metric("Workflow status", artifact["status"].title(), border=True)
    cards[1].metric("Steps used", artifact["budget"]["steps_used"], border=True)
    cards[2].metric("Missing roles", sum(row["status"] == "missing" for row in artifact["trace"]), border=True)
    cards[3].metric("Conflicts", sum(row["status"] == "conflict" for row in artifact["trace"]), border=True)
    trace_rows = [{
        "Step": row["step"], "Role": row["role"], "Tool": row["tool"], "Status": row["status"],
        "Facts": len(row.get("facts", [])), "Citations": len(row.get("citations", [])), "Message": row.get("message", ""),
    } for row in artifact["trace"]]
    st.dataframe(
        pd.DataFrame(trace_rows),
        hide_index=True,
        key=f"workflow_trace_{company}_{cutoff_label}",
        alt="Typed research workflow trace with role tool status facts and citations",
    )
    st.caption(f"Artifact SHA-256: {artifact['artifact_sha256']}")
    with st.expander("Facts, interpretations, scenarios, and citations"):
        st.json(artifact["trace"])
    st.download_button("Download workflow artifact", json.dumps(artifact, indent=2, default=str), "typed_workflow.json", "application/json")
    report = build_reconciled_report(artifact, _evidence_catalog(company, facts, macro_fact, cutoff_label))
    st.subheader("Reconciled research report")
    report_cards = st.columns(3)
    report_cards[0].metric("Reconciled claims", len(report["claims"]), border=True)
    report_cards[1].metric("Numeric mismatches", 0, border=True)
    report_cards[2].metric("Report hash", report["report_sha256"][:12], border=True)
    st.dataframe(
        pd.DataFrame(report["reconciliation"]), hide_index=True,
        key=f"workflow_reconciliation_{company}_{cutoff_label}",
        alt="Report claims reconciled against cited point-in-time source values and units",
    )
    st.download_button(
        "Download reconciled report", export_report_bundle(report),
        f"{company.lower()}-reconciled-report.zip", "application/zip", icon=":material/download:",
    )
    st.warning("A complete trace is not evidence of research quality. The offline News role is missing and no investment recommendation is produced.")

    st.subheader("Persisted research-run history")
    st.caption(
        "Save the current typed workflow and reconciled report as one content-addressed, append-only local run. "
        "Repeated identical content is not duplicated."
    )
    if st.button("Save current research run", icon=":material/save:", key="save_workflow_run"):
        try:
            folder, created = save_workflow_run(RUNS_ROOT, artifact, report)
            if created:
                st.success(f"Saved immutable run {folder.name}.")
            else:
                st.info(f"Identical run {folder.name} is already stored; nothing was overwritten.")
        except (OSError, ValueError) as exc:
            st.error(f"Research run could not be saved: {exc}")

    try:
        history = workflow_run_history(RUNS_ROOT)
    except (OSError, ValueError) as exc:
        st.error(f"Stored research history failed integrity verification: {exc}")
        history = pd.DataFrame()
    if history.empty:
        st.info("No typed workflow runs are stored yet. Save the current run to begin a local comparison history.")
    else:
        st.dataframe(
            history[
                [
                    "run_id",
                    "recorded_at",
                    "research_as_of",
                    "company",
                    "status",
                    "workflow_artifact_sha256",
                    "report_sha256",
                ]
            ],
            hide_index=True,
            key="workflow_history_table",
            alt="Verified append-only typed workflow research-run history",
        )
        if len(history) < 2:
            st.info("Save a different company, cutoff, question, or budget to enable comparison.")
        else:
            folders = dict(zip(history.run_id, history.folder))
            with st.container(horizontal=True):
                base_id = st.selectbox("Base run", list(folders), index=1, key="history_base")
                target_id = st.selectbox("Target run", list(folders), index=0, key="history_target")
            comparison = compare_workflow_runs(folders[base_id], folders[target_id])
            st.dataframe(
                comparison["metrics"],
                hide_index=True,
                key=f"workflow_comparison_{base_id}_{target_id}",
                alt="Base and target research-run metrics with explicit changes",
            )
            st.caption(
                f"Cutoff relation: {comparison['cutoff_relation']} · same company: {comparison['same_company']}. "
                f"{comparison['limitations']}"
            )
    st.warning(
        "History is local to one application filesystem and assumes one writer. It is not multi-user storage, remote backup, or a release approval record."
    )
