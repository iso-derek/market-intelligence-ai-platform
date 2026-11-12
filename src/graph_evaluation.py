"""Frozen graph-versus-table evaluation with point-in-time controls."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

try:
    from .evidence_graph import graph_as_of
except ImportError:  # Streamlit adds src/ directly to sys.path.
    from evidence_graph import graph_as_of


REQUIRED_CASE_COLUMNS = {
    "case_id", "start_id", "end_id", "as_of", "max_hops",
    "expected_found", "expected_relationships",
}


def load_graph_value_cases(path: str | Path) -> tuple[pd.DataFrame, str]:
    raw = Path(path).read_bytes()
    cases = pd.read_csv(path, dtype=str, keep_default_na=False)
    if set(cases.columns) != REQUIRED_CASE_COLUMNS:
        raise ValueError("invalid graph-value case schema")
    if cases.case_id.duplicated().any() or cases.empty:
        raise ValueError("graph-value case IDs must be unique and non-empty")
    cases["max_hops"] = pd.to_numeric(cases.max_hops, errors="raise").astype(int)
    if not cases.max_hops.between(1, 8).all():
        raise ValueError("max_hops must be between 1 and 8")
    lowered = cases.expected_found.str.lower()
    if not lowered.isin({"true", "false"}).all():
        raise ValueError("expected_found must be true or false")
    cases["expected_found"] = lowered.eq("true")
    return cases, hashlib.sha256(raw).hexdigest()


def _find_with_adjacency(edges: pd.DataFrame, start_id: str, end_id: str, max_hops: int) -> tuple[list[str] | None, int]:
    adjacency: dict[str, list[tuple[str, str]]] = {}
    for row in edges.itertuples(index=False):
        adjacency.setdefault(row.source_id, []).append((row.target_id, row.relationship))
    frontier = [(start_id, [start_id], [])]
    inspected = 0
    for _ in range(max_hops):
        following = []
        for node_id, path, relationships in frontier:
            outgoing = adjacency.get(node_id, [])
            inspected += len(outgoing)
            for target_id, relationship in outgoing:
                if target_id in path:
                    continue
                next_relationships = relationships + [relationship]
                if target_id == end_id:
                    return next_relationships, inspected
                following.append((target_id, path + [target_id], next_relationships))
        frontier = following
    return None, inspected


def _find_with_table_scan(edges: pd.DataFrame, start_id: str, end_id: str, max_hops: int) -> tuple[list[str] | None, int]:
    frontier = [(start_id, [start_id], [])]
    inspected = 0
    records = edges.to_dict("records")
    for _ in range(max_hops):
        following = []
        for node_id, path, relationships in frontier:
            inspected += len(records)
            for edge in records:
                if edge["source_id"] != node_id or edge["target_id"] in path:
                    continue
                target_id = edge["target_id"]
                next_relationships = relationships + [edge["relationship"]]
                if target_id == end_id:
                    return next_relationships, inspected
                following.append((target_id, path + [target_id], next_relationships))
        frontier = following
    return None, inspected


def evaluate_graph_value(nodes: pd.DataFrame, edges: pd.DataFrame, cases: pd.DataFrame, case_sha256: str) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for case in cases.itertuples(index=False):
        _, eligible_edges = graph_as_of(nodes, edges, case.as_of)
        expected = [item.strip() for item in case.expected_relationships.split(">") if item.strip()]
        graph_path, graph_inspected = _find_with_adjacency(
            eligible_edges, case.start_id, case.end_id, case.max_hops
        )
        table_path, table_inspected = _find_with_table_scan(
            eligible_edges, case.start_id, case.end_id, case.max_hops
        )
        graph_found = graph_path is not None
        table_found = table_path is not None
        rows.append({
            "case_id": case.case_id,
            "as_of": case.as_of,
            "expected_found": bool(case.expected_found),
            "graph_found": graph_found,
            "table_found": table_found,
            "graph_exact": graph_found == case.expected_found and (not graph_found or graph_path == expected),
            "table_exact": table_found == case.expected_found and (not table_found or table_path == expected),
            "method_parity": graph_path == table_path,
            "graph_relationships": " > ".join(graph_path or []),
            "table_relationships": " > ".join(table_path or []),
            "graph_edges_inspected": graph_inspected,
            "table_rows_inspected": table_inspected,
        })
    results = pd.DataFrame(rows)
    count = len(results)
    graph_total = int(results.graph_edges_inspected.sum())
    table_total = int(results.table_rows_inspected.sum())
    return {
        "case_sha256": case_sha256,
        "case_count": count,
        "graph_exact_rate": float(results.graph_exact.mean()),
        "table_exact_rate": float(results.table_exact.mean()),
        "method_parity_rate": float(results.method_parity.mean()),
        "graph_edges_inspected": graph_total,
        "table_rows_inspected": table_total,
        "inspection_reduction": 0.0 if table_total == 0 else 1.0 - graph_total / table_total,
        "conclusion": (
            "The graph adds no accuracy on this tiny authored fixture; it reduces repeated row inspection "
            "and makes multi-hop provenance explicit. This is regression evidence, not production-scale proof."
        ),
        "results": results,
    }
