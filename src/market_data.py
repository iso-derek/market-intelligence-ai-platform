"""Point-in-time market, macro, and fundamental analytics.

The module deliberately separates provider I/O from normalization and finance
arithmetic.  The bundled fixture provider is deterministic; future licensed or
public providers can implement the same contract without changing calculations.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

import numpy as np
import pandas as pd


PRICE_COLUMNS = {
    "instrument",
    "instrument_name",
    "date",
    "raw_close",
    "adjusted_close",
    "currency",
    "calendar",
    "available_at",
    "source",
    "source_version",
}
MACRO_COLUMNS = {
    "series_id",
    "series_name",
    "observation_date",
    "value",
    "unit",
    "release_at",
    "vintage_at",
    "available_at",
    "source",
}
FUNDAMENTAL_COLUMNS = {
    "company",
    "company_name",
    "sector",
    "fiscal_period_end",
    "filed_at",
    "available_at",
    "report_version",
    "metric",
    "value",
    "currency",
    "unit",
    "source",
}


@runtime_checkable
class MarketDataProvider(Protocol):
    """Provider boundary consumed by the analytics and dashboard layers."""

    def prices(self) -> pd.DataFrame: ...

    def macro(self) -> pd.DataFrame: ...

    def fundamentals(self) -> pd.DataFrame: ...


def _require_columns(frame: pd.DataFrame, required: set[str], label: str) -> None:
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"{label} data is missing columns: {', '.join(missing)}")


def _utc(series: pd.Series, label: str) -> pd.Series:
    parsed = pd.to_datetime(series, utc=True, errors="coerce")
    if parsed.isna().any():
        rows = parsed.index[parsed.isna()].tolist()
        raise ValueError(f"{label} contains invalid timestamps at rows {rows}")
    return parsed


def normalise_prices(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize daily close observations."""
    _require_columns(frame, PRICE_COLUMNS, "price")
    output = frame.copy()
    output["date"] = _utc(output["date"], "price date")
    output["available_at"] = _utc(output["available_at"], "price available_at")
    for column in ["raw_close", "adjusted_close"]:
        output[column] = pd.to_numeric(output[column], errors="coerce")
        if output[column].isna().any() or (output[column] <= 0).any():
            raise ValueError(f"{column} must contain positive numbers")
    for column in ["instrument", "currency", "calendar", "source", "source_version"]:
        if output[column].astype("string").str.strip().eq("").any():
            raise ValueError(f"{column} cannot be blank")
    if (output["available_at"] < output["date"]).any():
        raise ValueError("price availability cannot precede its market date")
    if output.duplicated(["instrument", "date", "source_version"]).any():
        raise ValueError("price observations must be unique by instrument, date, and source version")
    return output.sort_values(["instrument", "date", "available_at"]).reset_index(drop=True)


def normalise_macro(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate macro observations while preserving every vintage."""
    _require_columns(frame, MACRO_COLUMNS, "macro")
    output = frame.copy()
    for column in ["observation_date", "release_at", "vintage_at", "available_at"]:
        output[column] = _utc(output[column], f"macro {column}")
    output["value"] = pd.to_numeric(output["value"], errors="coerce")
    if output["value"].isna().any():
        raise ValueError("macro value must be numeric")
    if (output["release_at"] < output["observation_date"]).any():
        raise ValueError("macro release cannot precede its observation period")
    if (output["vintage_at"] < output["release_at"]).any():
        raise ValueError("macro vintage cannot precede its first release")
    if (output["available_at"] < output["vintage_at"]).any():
        raise ValueError("macro availability cannot precede its vintage")
    if output.duplicated(["series_id", "observation_date", "vintage_at"]).any():
        raise ValueError("macro vintages must be unique")
    return output.sort_values(["series_id", "observation_date", "vintage_at"]).reset_index(drop=True)


def normalise_fundamentals(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate long-form company facts while retaining restatements."""
    _require_columns(frame, FUNDAMENTAL_COLUMNS, "fundamental")
    output = frame.copy()
    for column in ["fiscal_period_end", "filed_at", "available_at"]:
        output[column] = _utc(output[column], f"fundamental {column}")
    output["report_version"] = pd.to_numeric(output["report_version"], errors="coerce")
    output["value"] = pd.to_numeric(output["value"], errors="coerce")
    if output[["report_version", "value"]].isna().any().any():
        raise ValueError("fundamental value and report_version must be numeric")
    if (output["report_version"] < 1).any():
        raise ValueError("report_version must be at least 1")
    if (output["filed_at"] < output["fiscal_period_end"]).any():
        raise ValueError("filing time cannot precede the fiscal period end")
    if (output["available_at"] < output["filed_at"]).any():
        raise ValueError("fundamental availability cannot precede filing time")
    keys = ["company", "fiscal_period_end", "report_version", "metric"]
    if output.duplicated(keys).any():
        raise ValueError("fundamental facts must be unique within each report version")
    return output.sort_values(keys + ["available_at"]).reset_index(drop=True)


@dataclass(frozen=True)
class FixtureProvider:
    """CSV-backed deterministic provider shipped for education and testing."""

    root: Path

    def prices(self) -> pd.DataFrame:
        return normalise_prices(pd.read_csv(self.root / "prices.csv"))

    def macro(self) -> pd.DataFrame:
        return normalise_macro(pd.read_csv(self.root / "macro_vintages.csv"))

    def fundamentals(self) -> pd.DataFrame:
        return normalise_fundamentals(pd.read_csv(self.root / "fundamentals.csv"))


def parse_cutoff(value: object) -> pd.Timestamp:
    """Return a timezone-aware UTC cutoff."""
    try:
        cutoff = pd.Timestamp(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("cutoff must be a valid date or timestamp") from exc
    if cutoff.tzinfo is None:
        cutoff = cutoff.tz_localize("UTC")
    else:
        cutoff = cutoff.tz_convert("UTC")
    return cutoff


def prices_as_of(frame: pd.DataFrame, cutoff: object) -> pd.DataFrame:
    """Return only price records demonstrably available by ``cutoff``."""
    prices = normalise_prices(frame)
    point = parse_cutoff(cutoff)
    eligible = prices.loc[(prices["available_at"] <= point) & (prices["date"] <= point)].copy()
    if eligible.empty:
        return eligible
    return (
        eligible.sort_values(["instrument", "date", "available_at", "source_version"])
        .drop_duplicates(["instrument", "date"], keep="last")
        .reset_index(drop=True)
    )


def macro_as_of(frame: pd.DataFrame, cutoff: object) -> pd.DataFrame:
    """Select the latest macro vintage known at a historical cutoff."""
    macro = normalise_macro(frame)
    point = parse_cutoff(cutoff)
    eligible = macro.loc[macro["available_at"] <= point].copy()
    if eligible.empty:
        return eligible
    return (
        eligible.sort_values(["series_id", "observation_date", "vintage_at", "available_at"])
        .drop_duplicates(["series_id", "observation_date"], keep="last")
        .reset_index(drop=True)
    )


def fundamentals_as_of(frame: pd.DataFrame, cutoff: object) -> pd.DataFrame:
    """Select the latest complete report version available at ``cutoff``.

    Selection happens at report-version level, then retains all metrics from the
    chosen version. This prevents a later restatement from leaking into an earlier
    historical view and avoids mixing facts from different report versions.
    """
    facts = normalise_fundamentals(frame)
    point = parse_cutoff(cutoff)
    eligible = facts.loc[facts["available_at"] <= point].copy()
    if eligible.empty:
        return eligible
    report_keys = ["company", "fiscal_period_end"]
    version_keys = report_keys + ["report_version"]
    expected_counts = facts.groupby(version_keys, as_index=False).agg(expected_facts=("metric", "count"))
    eligible_counts = eligible.groupby(version_keys, as_index=False).agg(eligible_facts=("metric", "count"))
    complete_versions = eligible_counts.merge(expected_counts, on=version_keys, how="inner")
    complete_versions = complete_versions.loc[
        complete_versions["eligible_facts"].eq(complete_versions["expected_facts"]), version_keys
    ]
    eligible = eligible.merge(complete_versions, on=version_keys, how="inner")
    if eligible.empty:
        return eligible
    versions = (
        eligible.groupby(report_keys, as_index=False)
        .agg(report_version=("report_version", "max"))
    )
    selected = eligible.merge(versions, on=report_keys + ["report_version"], how="inner")
    return selected.sort_values(report_keys + ["metric"]).reset_index(drop=True)


def price_performance(frame: pd.DataFrame, cutoff: object, periods_per_year: int = 252) -> pd.DataFrame:
    """Calculate adjusted-close return and annualized sample volatility.

    Simple returns are ``P_t / P_(t-1) - 1``. Volatility is the sample standard
    deviation of those returns multiplied by ``sqrt(periods_per_year)``.
    """
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    prices = prices_as_of(frame, cutoff)
    rows: list[dict[str, object]] = []
    for instrument, group in prices.groupby("instrument", sort=True):
        ordered = group.sort_values("date")
        returns = ordered["adjusted_close"].pct_change().dropna()
        volatility = returns.std(ddof=1) * np.sqrt(periods_per_year) if len(returns) >= 2 else np.nan
        rows.append(
            {
                "instrument": instrument,
                "instrument_name": ordered["instrument_name"].iloc[-1],
                "currency": ordered["currency"].iloc[-1],
                "calendar": ordered["calendar"].iloc[-1],
                "first_date": ordered["date"].iloc[0],
                "latest_date": ordered["date"].iloc[-1],
                "latest_adjusted_close": ordered["adjusted_close"].iloc[-1],
                "cumulative_return": ordered["adjusted_close"].iloc[-1] / ordered["adjusted_close"].iloc[0] - 1,
                "annualized_volatility": volatility,
                "observations": len(ordered),
                "available_at": ordered["available_at"].max(),
                "source": ordered["source"].iloc[-1],
            }
        )
    return pd.DataFrame(rows)


def fundamental_ratios(frame: pd.DataFrame, cutoff: object) -> pd.DataFrame:
    """Calculate comparable ratios from point-in-time company facts."""
    facts = fundamentals_as_of(frame, cutoff)
    if facts.empty:
        return pd.DataFrame()
    latest_periods = facts.groupby("company")["fiscal_period_end"].transform("max")
    latest = facts.loc[facts["fiscal_period_end"].eq(latest_periods)].copy()
    dimensions = [
        "company",
        "company_name",
        "sector",
        "fiscal_period_end",
        "report_version",
        "currency",
        "unit",
        "available_at",
        "source",
    ]
    wide = latest.pivot_table(index=dimensions, columns="metric", values="value", aggfunc="first").reset_index()
    required = {"revenue", "net_income", "current_assets", "current_liabilities", "total_debt", "shareholders_equity"}
    missing = sorted(required.difference(wide.columns))
    if missing:
        raise ValueError(f"cannot calculate ratios; missing metrics: {', '.join(missing)}")
    if (wide[["revenue", "current_liabilities", "shareholders_equity"]].eq(0)).any().any():
        raise ValueError("ratio denominators cannot be zero")
    wide["net_margin"] = wide["net_income"] / wide["revenue"]
    wide["current_ratio"] = wide["current_assets"] / wide["current_liabilities"]
    wide["debt_to_equity"] = wide["total_debt"] / wide["shareholders_equity"]
    columns = dimensions + ["revenue", "net_income", "net_margin", "current_ratio", "debt_to_equity"]
    return wide[columns].sort_values("company").reset_index(drop=True)
