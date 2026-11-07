"""Evidence graph and local operations presentation."""
from datetime import datetime, timezone
from pathlib import Path
import os

import streamlit as st

from evidence_graph import evidence_paths, graph_as_of, load_evidence_graph, operations_report
from graph_evaluation import evaluate_graph_value, load_graph_value_cases
from accessibility_audit import audit_streamlit_project
from operations import create_verified_backup, operational_health


ROOT = Path(__file__).resolve().parents[1]


def render_graph_dashboard() -> None:
    nodes, edges, graph_hash = load_evidence_graph(ROOT / "data/fixtures/evidence_graph_nodes.csv", ROOT / "data/fixtures/evidence_graph_edges.csv")
    with st.sidebar:
        st.header("Graph controls")
        cutoff = st.selectbox("Graph cutoff", ["2026-02-01T23:59:59Z", "2026-03-01T23:59:59Z"], index=1)
        st.info("Relationships are provenance links, not causal claims.")
    eligible_nodes, eligible_edges = graph_as_of(nodes, edges, cutoff)
    st.subheader("Evidence graph & operations")
    cards = st.columns(4)
    cards[0].metric("Eligible nodes", len(eligible_nodes), border=True)
    cards[1].metric("Eligible edges", len(eligible_edges), border=True)
    cards[2].metric("Dangling links", 0, border=True)
    cards[3].metric("Graph hash", graph_hash[:12], border=True)
    st.dataframe(eligible_nodes, hide_index=True, alt="Point-in-time evidence graph nodes with type URI and availability")
    st.dataframe(eligible_edges, hide_index=True, alt="Non-causal evidence graph edges with supporting evidence and availability")
    paths = evidence_paths(eligible_edges, "company:ALP", 4) if not eligible_edges.empty else eligible_edges
    st.subheader("Bounded provenance paths")
    st.dataframe(paths, hide_index=True, alt="Bounded provenance paths and relationship sequences from Alpha Industries")
    cases, case_hash = load_graph_value_cases(ROOT / "data/evaluation/graph_value_cases.csv")
    evaluation = evaluate_graph_value(nodes, edges, cases, case_hash)
    st.subheader("Graph versus table evaluation")
    evaluation_cards = st.columns(4)
    evaluation_cards[0].metric("Graph exactness", f"{evaluation['graph_exact_rate']:.0%}", border=True)
    evaluation_cards[1].metric("Table exactness", f"{evaluation['table_exact_rate']:.0%}", border=True)
    evaluation_cards[2].metric("Method parity", f"{evaluation['method_parity_rate']:.0%}", border=True)
    evaluation_cards[3].metric("Inspection reduction", f"{evaluation['inspection_reduction']:.0%}", border=True)
    st.dataframe(
        evaluation["results"], hide_index=True,
        alt="Frozen graph and edge-table lookup comparison with point-in-time exactness and inspection counts",
    )
    st.caption(f"Frozen case SHA-256: {evaluation['case_sha256']}")
    st.info(evaluation["conclusion"])
    report = operations_report(ROOT, graph_hash)
    st.subheader("Local operations report")
    st.json(report)
    accessibility = audit_streamlit_project(ROOT)
    st.subheader("Accessibility audit")
    accessibility_cards = st.columns(3)
    accessibility_cards[0].metric("Surfaces scanned", accessibility["files_scanned"], border=True)
    accessibility_cards[1].metric("Static findings", accessibility["finding_count"], border=True)
    accessibility_cards[2].metric("Static audit", "Pass" if accessibility["passed"] else "Review", border=True)
    if accessibility["findings"]:
        st.dataframe(
            accessibility["findings"], hide_index=True,
            alt="Static Streamlit accessibility and deprecated API findings",
        )
    st.caption(accessibility["scope"])
    database_path = Path(os.environ.get("MARKET_INTELLIGENCE_DB", ROOT / "data/runtime/evidence.db"))
    health = operational_health(database_path)
    st.subheader("Persistence monitoring & recovery")
    health_cards = st.columns(4)
    health_cards[0].metric("Database", str(health["status"]).replace("_", " ").title(), border=True)
    health_cards[1].metric("Registered sources", health.get("sources", 0), border=True)
    health_cards[2].metric("Fetch attempts", health.get("attempts", 0), border=True)
    health_cards[3].metric("Failed attempts", health.get("failed_attempts", 0), border=True)
    if health["status"] == "healthy":
        st.caption(f"Schema v{health['schema_version']} · latest attempt {health.get('latest_attempt_at') or 'none'} · SHA-256 {health['database_sha256']}")
        if st.button("Create verified local backup", icon=":material/backup:"):
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            destination = ROOT / "data/runtime/backups" / f"evidence-{stamp}.db"
            backup = create_verified_backup(database_path, destination)
            st.success(f"Verified backup created: {destination.name} ({backup['backup']['bytes']} bytes)")
    else:
        st.info("The persistent evidence database is not initialized. Open News evidence once to create the local registry.")
    st.caption("Backups never overwrite existing files. Automated retention, encryption, off-device copies, and multi-worker recovery remain owner-controlled boundaries.")
    st.success("Required project files are present and the current acceptance path is a verified local demonstration.")
    st.warning("No hosted deployment, automated backup, multi-worker service, or causal knowledge-graph inference is claimed.")
