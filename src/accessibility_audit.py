"""Small static accessibility and deprecated-API audit for Streamlit surfaces."""
from __future__ import annotations

import ast
from pathlib import Path


ALT_REQUIRED = {
    "dataframe", "data_editor", "table", "line_chart", "bar_chart", "area_chart",
    "scatter_chart", "altair_chart", "vega_lite_chart", "plotly_chart", "echarts_chart",
    "graphviz_chart", "map", "pydeck_chart", "mermaid_chart", "image", "pyplot",
    "video", "audio", "pdf", "iframe",
}
LABELLED_WIDGETS = {
    "button", "checkbox", "date_input", "file_uploader", "multiselect", "number_input",
    "radio", "segmented_control", "selectbox", "slider", "text_area", "text_input", "toggle",
}


def _streamlit_method(call: ast.Call) -> str | None:
    target = call.func
    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "st":
        return target.attr
    if (
        isinstance(target, ast.Attribute) and isinstance(target.value, ast.Attribute)
        and isinstance(target.value.value, ast.Name) and target.value.value.id == "st"
        and target.value.attr == "sidebar"
    ):
        return target.attr
    return None


def audit_streamlit_file(path: str | Path) -> list[dict[str, object]]:
    path = Path(path)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    findings: list[dict[str, object]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        method = _streamlit_method(node)
        if method is None:
            continue
        keywords = {item.arg: item.value for item in node.keywords if item.arg}
        if method in ALT_REQUIRED and "alt" not in keywords:
            findings.append({"file": path.name, "line": node.lineno, "rule": "missing-alt", "method": method})
        if "use_container_width" in keywords:
            findings.append({"file": path.name, "line": node.lineno, "rule": "deprecated-width", "method": method})
        if method in LABELLED_WIDGETS and node.args:
            label = node.args[0]
            if isinstance(label, ast.Constant) and isinstance(label.value, str) and not label.value.strip():
                findings.append({"file": path.name, "line": node.lineno, "rule": "empty-label", "method": method})
        unsafe = keywords.get("unsafe_allow_html")
        if isinstance(unsafe, ast.Constant) and unsafe.value is True:
            findings.append({"file": path.name, "line": node.lineno, "rule": "unsafe-html", "method": method})
    return findings


def audit_streamlit_project(root: str | Path) -> dict[str, object]:
    root = Path(root)
    files = [root / "app.py", *sorted((root / "src").glob("*dashboard.py"))]
    findings = [item for path in files for item in audit_streamlit_file(path)]
    return {
        "files_scanned": len(files), "finding_count": len(findings),
        "passed": not findings, "findings": findings,
        "scope": "Static labels, alt names, deprecated width API, and unsafe HTML; browser walkthrough is separate evidence.",
    }
