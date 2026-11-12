"""Deterministic company stress scenarios with explicit bounded assumptions."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json

import pandas as pd


@dataclass(frozen=True)
class ScenarioAssumptions:
    """Independent shocks expressed as decimals except for margin basis points."""

    revenue_shock: float = 0.0
    margin_shock_bps: int = 0
    current_assets_shock: float = 0.0
    current_liabilities_shock: float = 0.0
    debt_shock: float = 0.0
    equity_shock: float = 0.0

    def __post_init__(self) -> None:
        bounds = {
            "revenue_shock": (-0.50, 0.50),
            "margin_shock_bps": (-2_000, 2_000),
            "current_assets_shock": (-0.50, 0.50),
            "current_liabilities_shock": (-0.50, 0.50),
            "debt_shock": (-0.50, 1.00),
            "equity_shock": (-0.50, 0.50),
        }
        for field, (lower, upper) in bounds.items():
            value = getattr(self, field)
            if not lower <= value <= upper:
                raise ValueError(f"{field} must be between {lower} and {upper}")


SCENARIO_PRESETS = {
    "Neutral": ScenarioAssumptions(),
    "Downside": ScenarioAssumptions(
        revenue_shock=-0.10,
        margin_shock_bps=-300,
        current_assets_shock=-0.10,
        current_liabilities_shock=0.10,
        debt_shock=0.20,
        equity_shock=-0.10,
    ),
    "Recovery": ScenarioAssumptions(
        revenue_shock=0.08,
        margin_shock_bps=200,
        current_assets_shock=0.05,
        current_liabilities_shock=-0.05,
        debt_shock=-0.10,
        equity_shock=0.08,
    ),
}


def stress_watchlist(snapshot: pd.DataFrame, assumptions: ScenarioAssumptions) -> pd.DataFrame:
    """Apply transparent shocks to each complete watchlist company row."""
    required = {
        "ticker",
        "company_name",
        "revenue",
        "net_income",
        "net_margin",
        "current_ratio",
        "debt_to_equity",
        "filing_currency",
        "filing_unit",
        "cutoff",
    }
    missing = sorted(required.difference(snapshot.columns))
    if missing:
        raise ValueError(f"watchlist snapshot is missing columns: {', '.join(missing)}")
    if snapshot.empty:
        raise ValueError("watchlist snapshot cannot be empty")
    numeric = ["revenue", "net_income", "net_margin", "current_ratio", "debt_to_equity"]
    if snapshot[numeric].isna().any().any():
        raise ValueError("scenario analysis requires complete fundamental values")

    output = snapshot.copy()
    output["stressed_revenue"] = output["revenue"] * (1 + assumptions.revenue_shock)
    output["stressed_net_margin"] = output["net_margin"] + assumptions.margin_shock_bps / 10_000
    if output["stressed_net_margin"].abs().gt(1).any():
        raise ValueError("stressed net margin must remain between -100% and 100%")
    output["stressed_net_income"] = output["stressed_revenue"] * output["stressed_net_margin"]
    output["net_income_change"] = output["stressed_net_income"] - output["net_income"]
    output["stressed_current_ratio"] = (
        output["current_ratio"]
        * (1 + assumptions.current_assets_shock)
        / (1 + assumptions.current_liabilities_shock)
    )
    output["stressed_debt_to_equity"] = (
        output["debt_to_equity"] * (1 + assumptions.debt_shock) / (1 + assumptions.equity_shock)
    )
    output["revenue_shock"] = assumptions.revenue_shock
    output["margin_shock_bps"] = assumptions.margin_shock_bps
    output["current_assets_shock"] = assumptions.current_assets_shock
    output["current_liabilities_shock"] = assumptions.current_liabilities_shock
    output["debt_shock"] = assumptions.debt_shock
    output["equity_shock"] = assumptions.equity_shock

    return output[
        [
            "ticker",
            "company_name",
            "filing_currency",
            "filing_unit",
            "revenue",
            "stressed_revenue",
            "net_margin",
            "stressed_net_margin",
            "net_income",
            "stressed_net_income",
            "net_income_change",
            "current_ratio",
            "stressed_current_ratio",
            "debt_to_equity",
            "stressed_debt_to_equity",
            "revenue_shock",
            "margin_shock_bps",
            "current_assets_shock",
            "current_liabilities_shock",
            "debt_shock",
            "equity_shock",
            "cutoff",
        ]
    ].sort_values("ticker").reset_index(drop=True)


def scenario_hash(results: pd.DataFrame, assumptions: ScenarioAssumptions) -> str:
    """Return a stable identity covering assumptions and sorted scenario results."""
    records: list[dict[str, object]] = []
    for row in results.sort_values("ticker").to_dict(orient="records"):
        record: dict[str, object] = {}
        for key in sorted(row):
            value = row[key]
            if pd.isna(value):
                record[key] = None
            elif isinstance(value, pd.Timestamp):
                record[key] = value.isoformat()
            elif hasattr(value, "item"):
                record[key] = value.item()
            else:
                record[key] = value
        records.append(record)
    payload = {"assumptions": asdict(assumptions), "results": records, "version": "deterministic-stress-v1"}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
