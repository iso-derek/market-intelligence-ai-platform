"""Streamlit inspector for the bounded typed workflow engine."""
import json

import pandas as pd
import streamlit as st

from workflows import WorkflowRequest, make_demo_tools, run_workflow


COMPANY_FACTS = {
    "ALP": [
        {"fact_key": "revenue", "value": 1000, "unit": "USD million", "evidence_ids": ["filing-alp-2025:p1:s1"]},
        {"fact_key": "net_income", "value": 90, "unit": "USD million", "evidence_ids": ["filing-alp-2025:p3:s1"]},
    ],
    "BET": [{"fact_key": "revenue", "value": 800, "unit": "USD million", "evidence_ids": ["filing-bet-2025:p1:s1"]}],
    "GAM": [{"fact_key": "revenue", "value": 600, "unit": "USD million", "evidence_ids": ["filing-gam-2025:p1:s1"]}],
}
RISK_IDS = {"ALP": "filing-alp-2025:p2:s2", "BET": "filing-bet-2025:p2:s2", "GAM": "filing-gam-2025:p2:s2"}


def render_workflow_dashboard() -> None:
    st.subheader("Bounded research workflow")
    st.caption("Five typed roles, fixed tool allowlists, explicit budgets, and a hash-identified trace. No autonomous model is invoked.")
    with st.sidebar:
        st.header("Workflow controls")
        company = st.selectbox("Company", list(COMPANY_FACTS), format_func=lambda value: {"ALP": "Alpha Industries", "BET": "Beta Retail", "GAM": "Gamma Software"}[value])
        max_seconds = st.slider("Time budget (seconds)", 1, 10, 5)
        st.info("The News role is deliberately missing in this offline demonstration; the trace keeps that gap visible.")
    question = st.text_input("Research question", f"What is the evidence-backed outlook and risk context for {company}?")
    macro = [{"fact_key": "cpi", "value": 3.0, "unit": "% year over year", "evidence_ids": ["macro:CPI:2026-01:2026-02-20"]}]
    risks = [{"evidence_id": RISK_IDS[company], "kind": "filing_risk_factor"}]
    request = WorkflowRequest(question, "2026-03-01T23:59:59Z", company, max_steps=5, max_seconds=float(max_seconds))
    artifact = run_workflow(request, make_demo_tools(COMPANY_FACTS[company], macro, risks))

    cards = st.columns(4)
    cards[0].metric("Workflow status", artifact["status"].title(), border=True)
    cards[1].metric("Steps used", artifact["budget"]["steps_used"], border=True)
    cards[2].metric("Missing roles", sum(row["status"] == "missing" for row in artifact["trace"]), border=True)
    cards[3].metric("Conflicts", sum(row["status"] == "conflict" for row in artifact["trace"]), border=True)
    trace_rows = [{
        "Step": row["step"], "Role": row["role"], "Tool": row["tool"], "Status": row["status"],
        "Facts": len(row.get("facts", [])), "Citations": len(row.get("citations", [])), "Message": row.get("message", ""),
    } for row in artifact["trace"]]
    st.dataframe(pd.DataFrame(trace_rows), hide_index=True, alt="Typed research workflow trace with role tool status facts and citations")
    st.caption(f"Artifact SHA-256: {artifact['artifact_sha256']}")
    with st.expander("Facts, interpretations, scenarios, and citations"):
        st.json(artifact["trace"])
    st.download_button("Download workflow artifact", json.dumps(artifact, indent=2, default=str), "typed_workflow.json", "application/json")
    st.warning("A complete trace is not evidence of research quality. The offline News role is missing and no investment recommendation is produced.")
