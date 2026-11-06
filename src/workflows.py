"""Typed, budgeted research workflows with auditable traces."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import time
from typing import Callable

import pandas as pd


STATUSES = {"success", "missing", "conflict", "error"}


@dataclass(frozen=True)
class WorkflowRequest:
    question: str
    as_of: str
    company: str
    max_steps: int = 5
    max_seconds: float = 5.0


@dataclass(frozen=True)
class WorkflowStep:
    role: str
    tool: str


@dataclass
class ToolResult:
    status: str
    facts: list[dict[str, object]]
    citations: list[dict[str, object]]
    interpretations: list[str]
    scenarios: list[str]
    message: str = ""


ROLE_SPECS = {
    "Company": {"company_facts"},
    "Macro": {"macro_snapshot"},
    "News": {"news_evidence"},
    "Risk": {"risk_evidence"},
    "Synthesis": {"synthesize"},
}
DEFAULT_PLAN = [
    WorkflowStep("Company", "company_facts"),
    WorkflowStep("Macro", "macro_snapshot"),
    WorkflowStep("News", "news_evidence"),
    WorkflowStep("Risk", "risk_evidence"),
    WorkflowStep("Synthesis", "synthesize"),
]
Tool = Callable[[WorkflowRequest, list[dict[str, object]]], ToolResult]


def _validate_result(result: ToolResult) -> None:
    if result.status not in STATUSES:
        raise ValueError(f"invalid tool status: {result.status}")
    for fact in result.facts:
        if not {"fact_key", "value", "unit", "evidence_ids"}.issubset(fact):
            raise ValueError("facts require fact_key, value, unit, and evidence_ids")
        if not fact["evidence_ids"] or not all(str(item).strip() for item in fact["evidence_ids"]):
            raise ValueError("every fact must identify supporting evidence")


def run_workflow(
    request: WorkflowRequest,
    tools: dict[str, Tool],
    plan: list[WorkflowStep] | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> dict[str, object]:
    """Execute an explicit plan while enforcing role allowlists and budgets."""
    if not request.question.strip() or not request.company.strip():
        raise ValueError("question and company are required")
    if request.max_steps < 1 or request.max_seconds <= 0:
        raise ValueError("workflow budgets must be positive")
    point = pd.Timestamp(request.as_of)
    point = point.tz_localize("UTC") if point.tzinfo is None else point.tz_convert("UTC")
    steps = list(plan or DEFAULT_PLAN)
    if len(steps) > request.max_steps:
        raise ValueError("plan exceeds max_steps budget")
    started = clock()
    trace: list[dict[str, object]] = []
    for index, step in enumerate(steps, start=1):
        if step.role not in ROLE_SPECS or step.tool not in ROLE_SPECS[step.role]:
            raise PermissionError(f"{step.role} is not allowed to call {step.tool}")
        if step.tool not in tools:
            raise ValueError(f"tool is not registered: {step.tool}")
        if clock() - started > request.max_seconds:
            trace.append({"step": index, "role": step.role, "tool": step.tool, "status": "error", "message": "time budget exceeded"})
            break
        try:
            result = tools[step.tool](request, trace)
            _validate_result(result)
        except Exception as exc:
            result = ToolResult("error", [], [], [], [], f"{type(exc).__name__}: {exc}")
        trace.append({"step": index, "role": step.role, "tool": step.tool, **asdict(result)})
    payload = {
        "request": {**asdict(request), "as_of": point.isoformat()},
        "plan": [asdict(step) for step in steps],
        "trace": trace,
        "budget": {"max_steps": request.max_steps, "max_seconds": request.max_seconds, "steps_used": len(trace)},
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    payload["artifact_sha256"] = hashlib.sha256(canonical).hexdigest()
    payload["status"] = "error" if any(row["status"] == "error" for row in trace) else (
        "conflict" if any(row["status"] == "conflict" for row in trace) else "complete"
    )
    return payload


def make_demo_tools(company_facts: list[dict], macro_facts: list[dict], risk_citations: list[dict]) -> dict[str, Tool]:
    """Build deterministic local handlers for the dashboard demonstration."""
    def company(_: WorkflowRequest, __: list[dict]) -> ToolResult:
        return ToolResult("success" if company_facts else "missing", company_facts, [], [], [], "Point-in-time company facts")

    def macro(_: WorkflowRequest, __: list[dict]) -> ToolResult:
        return ToolResult("success" if macro_facts else "missing", macro_facts, [], [], [], "Point-in-time macro snapshot")

    def news(_: WorkflowRequest, __: list[dict]) -> ToolResult:
        return ToolResult("missing", [], [], [], [], "No non-synthetic news evidence loaded in the offline demonstration")

    def risk(_: WorkflowRequest, __: list[dict]) -> ToolResult:
        return ToolResult("success" if risk_citations else "missing", [], risk_citations, [], ["Risk language is a scenario, not a probability estimate."], "Filing risk evidence")

    def synthesis(_: WorkflowRequest, trace: list[dict]) -> ToolResult:
        facts = [fact for row in trace for fact in row.get("facts", [])]
        values: dict[str, set[str]] = {}
        for fact in facts:
            values.setdefault(str(fact["fact_key"]), set()).add(str(fact["value"]))
        conflicts = sorted(key for key, seen in values.items() if len(seen) > 1)
        if conflicts:
            return ToolResult("conflict", [], [], [], [], f"Conflicting values for: {', '.join(conflicts)}")
        citations = [citation for row in trace for citation in row.get("citations", [])]
        return ToolResult("success", facts, citations, ["Facts and scenarios remain separated in this trace."], [], "Evidence-preserving synthesis")

    return {
        "company_facts": company, "macro_snapshot": macro, "news_evidence": news,
        "risk_evidence": risk, "synthesize": synthesis,
    }
