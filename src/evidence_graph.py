"""Small provenance graph with point-in-time and non-causal safeguards."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


ALLOWED_RELATIONSHIPS = {"filed", "contains", "supports", "describes", "linked_to"}
CAUSAL_TERMS = {"caused", "causes", "drove", "impacted", "led_to"}


def load_evidence_graph(nodes_path: str | Path, edges_path: str | Path) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    nodes = pd.read_csv(nodes_path, dtype=str, keep_default_na=False)
    edges = pd.read_csv(edges_path, dtype=str, keep_default_na=False)
    if not {"node_id", "node_type", "label", "evidence_uri", "available_at"}.issubset(nodes.columns):
        raise ValueError("invalid graph node schema")
    if not {"edge_id", "source_id", "target_id", "relationship", "evidence_id", "available_at"}.issubset(edges.columns):
        raise ValueError("invalid graph edge schema")
    if nodes.node_id.duplicated().any() or edges.edge_id.duplicated().any():
        raise ValueError("graph identifiers must be unique")
    known = set(nodes.node_id)
    dangling = set(edges.source_id).union(edges.target_id).union(edges.evidence_id).difference(known)
    if dangling:
        raise ValueError(f"dangling graph references: {sorted(dangling)}")
    if not set(edges.relationship).issubset(ALLOWED_RELATIONSHIPS) or set(edges.relationship).intersection(CAUSAL_TERMS):
        raise ValueError("graph relationship is not allowed")
    nodes["available_at"] = pd.to_datetime(nodes.available_at, utc=True, errors="raise")
    edges["available_at"] = pd.to_datetime(edges.available_at, utc=True, errors="raise")
    payload = {"nodes": nodes.astype(str).to_dict("records"), "edges": edges.astype(str).to_dict("records")}
    graph_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return nodes, edges, graph_hash


def graph_as_of(nodes: pd.DataFrame, edges: pd.DataFrame, cutoff: object) -> tuple[pd.DataFrame, pd.DataFrame]:
    point = pd.Timestamp(cutoff)
    point = point.tz_localize("UTC") if point.tzinfo is None else point.tz_convert("UTC")
    eligible_nodes = nodes.loc[nodes.available_at.le(point)].copy()
    ids = set(eligible_nodes.node_id)
    eligible_edges = edges.loc[edges.available_at.le(point) & edges.source_id.isin(ids) & edges.target_id.isin(ids) & edges.evidence_id.isin(ids)].copy()
    return eligible_nodes.reset_index(drop=True), eligible_edges.reset_index(drop=True)


def evidence_paths(edges: pd.DataFrame, start_id: str, max_hops: int = 4) -> pd.DataFrame:
    if max_hops < 1 or max_hops > 8:
        raise ValueError("max_hops must be between 1 and 8")
    paths = [{"node_id": start_id, "path": [start_id], "relationships": []}]
    output = []
    for _ in range(max_hops):
        next_paths = []
        for item in paths:
            for edge in edges.loc[edges.source_id.eq(item["node_id"])].to_dict("records"):
                if edge["target_id"] in item["path"]:
                    continue
                expanded = {"node_id": edge["target_id"], "path": item["path"] + [edge["target_id"]], "relationships": item["relationships"] + [edge["relationship"]]}
                next_paths.append(expanded)
                output.append({"start_id": start_id, "end_id": edge["target_id"], "hops": len(expanded["relationships"]),
                               "path": " → ".join(expanded["path"]), "relationships": " → ".join(expanded["relationships"])})
        paths = next_paths
    return pd.DataFrame(output)


def operations_report(root: str | Path, graph_hash: str) -> dict[str, object]:
    root = Path(root)
    required = ["README.md", "docs/ROADMAP.md", "docs/DEVELOPMENT_STATUS.md", "app.py", "requirements.txt"]
    present = {item: (root / item).is_file() for item in required}
    return {"required_files": present, "required_files_ok": all(present.values()), "graph_sha256": graph_hash,
            "local_demo_url": "http://127.0.0.1:8503", "deployment_status": "verified_local_demo_not_hosted"}
