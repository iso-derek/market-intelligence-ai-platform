"""Point-in-time fixed-income and foreign-exchange fixture analytics."""
from pathlib import Path

import pandas as pd


REQUIRED = {"observation_id", "kind", "instrument", "date", "value", "unit", "tenor", "benchmark", "base_currency", "quote_currency", "available_at", "source"}


def load_rates_fx(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = REQUIRED.difference(frame.columns)
    if missing:
        raise ValueError(f"rates/FX data missing columns: {sorted(missing)}")
    if frame.observation_id.duplicated().any():
        raise ValueError("observation_id must be unique")
    frame["date"] = pd.to_datetime(frame["date"], utc=True, errors="raise")
    frame["available_at"] = pd.to_datetime(frame["available_at"], utc=True, errors="raise")
    frame["value"] = pd.to_numeric(frame["value"], errors="raise")
    if (frame.value <= 0).any() or (frame.available_at < frame.date).any():
        raise ValueError("values must be positive and availability cannot precede observation time")
    fx = frame.kind.eq("fx_spot")
    expected_units = frame.loc[fx, "quote_currency"] + " per " + frame.loc[fx, "base_currency"]
    if frame.loc[fx, "base_currency"].eq("").any() or frame.loc[fx, "quote_currency"].eq("").any() or not frame.loc[fx, "unit"].equals(expected_units):
        raise ValueError("FX rows require explicit BASE/QUOTE currencies and QUOTE per BASE units")
    yields = frame.kind.isin(["government_yield", "corporate_yield"])
    if not frame.loc[yields, "unit"].eq("percent").all() or frame.loc[yields, "tenor"].eq("").any():
        raise ValueError("yield rows require percent units and tenor")
    return frame.sort_values(["kind", "instrument", "date"]).reset_index(drop=True)


def rates_fx_as_of(frame: pd.DataFrame, cutoff: object) -> pd.DataFrame:
    point = pd.Timestamp(cutoff)
    point = point.tz_localize("UTC") if point.tzinfo is None else point.tz_convert("UTC")
    eligible = frame.loc[frame.available_at.le(point)].copy()
    return eligible.sort_values(["instrument", "date"]).drop_duplicates("instrument", keep="last").reset_index(drop=True)


def yield_curve(frame: pd.DataFrame, cutoff: object) -> pd.DataFrame:
    latest = rates_fx_as_of(frame, cutoff)
    return latest.loc[latest.kind.eq("government_yield"), ["instrument", "tenor", "value", "unit", "date", "available_at", "source"]].reset_index(drop=True)


def credit_spreads(frame: pd.DataFrame, cutoff: object) -> pd.DataFrame:
    latest = rates_fx_as_of(frame, cutoff)
    rows = []
    for corporate in latest.loc[latest.kind.eq("corporate_yield")].itertuples(index=False):
        benchmark = latest.loc[latest.instrument.eq(corporate.benchmark)]
        if len(benchmark) != 1:
            raise ValueError(f"missing unique benchmark for {corporate.instrument}")
        government = benchmark.iloc[0]
        rows.append({"instrument": corporate.instrument, "tenor": corporate.tenor, "yield_percent": corporate.value,
                     "benchmark": corporate.benchmark, "benchmark_yield_percent": government.value,
                     "spread_bps": (corporate.value - government.value) * 100,
                     "available_at": max(corporate.available_at, government.available_at)})
    return pd.DataFrame(rows)


def fx_performance(frame: pd.DataFrame, cutoff: object) -> pd.DataFrame:
    point = pd.Timestamp(cutoff)
    point = point.tz_localize("UTC") if point.tzinfo is None else point.tz_convert("UTC")
    eligible = frame.loc[frame.kind.eq("fx_spot") & frame.available_at.le(point)].sort_values(["instrument", "date"])
    rows = []
    for instrument, group in eligible.groupby("instrument", sort=True):
        if len(group) < 2:
            continue
        first, last = group.iloc[0], group.iloc[-1]
        change = last.value / first.value - 1
        rows.append({"instrument": instrument, "base_currency": last.base_currency, "quote_currency": last.quote_currency,
                     "unit": last.unit, "first_value": first.value, "latest_value": last.value, "base_return": change,
                     "interpretation": f"{last.base_currency} strengthened versus {last.quote_currency}" if change > 0 else f"{last.base_currency} weakened versus {last.quote_currency}",
                     "available_at": last.available_at})
    return pd.DataFrame(rows)
