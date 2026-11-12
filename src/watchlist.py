"""Point-in-time analyst watchlists for the bounded finance fixture."""
from __future__ import annotations

import hashlib
import json
import re
from typing import Iterable

import pandas as pd

from market_data import fundamental_ratios, parse_cutoff, price_performance, prices_as_of


def company_universe(
    registry: pd.DataFrame,
    prices: pd.DataFrame,
    cutoff: object,
) -> pd.DataFrame:
    """Return registry companies that are active and have fixture price coverage."""
    required = {"entity_id", "canonical_name", "ticker", "sector", "aliases", "active_from", "active_to"}
    missing = sorted(required.difference(registry.columns))
    if missing:
        raise ValueError(f"company registry is missing columns: {', '.join(missing)}")
    if "instrument" not in prices:
        raise ValueError("price data is missing instrument")

    point = parse_cutoff(cutoff)
    output = registry.copy()
    output["active_from"] = pd.to_datetime(output["active_from"], utc=True, errors="coerce")
    output["active_to"] = pd.to_datetime(output["active_to"], utc=True, errors="coerce")
    if output["active_from"].isna().any():
        raise ValueError("active_from must contain valid timestamps")
    price_tickers = set(prices["instrument"].astype("string").str.upper())
    active = output["active_from"].le(point) & (output["active_to"].isna() | output["active_to"].ge(point))
    output = output.loc[active & output["ticker"].str.upper().isin(price_tickers)].copy()
    return output.sort_values(["canonical_name", "ticker"]).reset_index(drop=True)


def _tokens(value: object) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", str(value).casefold()))


def search_companies(
    universe: pd.DataFrame,
    query: object = "",
    sectors: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Search by complete ticker/name/sector/alias tokens without fuzzy guesses."""
    required = {"canonical_name", "ticker", "sector", "aliases"}
    missing = sorted(required.difference(universe.columns))
    if missing:
        raise ValueError(f"company universe is missing columns: {', '.join(missing)}")

    output = universe.copy()
    selected_sectors = {str(value).strip() for value in sectors or [] if str(value).strip()}
    if selected_sectors:
        output = output.loc[output["sector"].isin(selected_sectors)]

    query_tokens = _tokens(query)
    if query_tokens:
        searchable = output[["canonical_name", "ticker", "sector", "aliases"]].apply(
            lambda row: set().union(*(_tokens(value) for value in row)), axis=1
        )
        output = output.loc[searchable.map(query_tokens.issubset)]
    return output.reset_index(drop=True)


def _selected_tickers(tickers: Iterable[object]) -> list[str]:
    selected = sorted({str(ticker).strip().upper() for ticker in tickers if str(ticker).strip()})
    if not selected:
        raise ValueError("select at least one watchlist company")
    return selected


def watchlist_snapshot(
    prices: pd.DataFrame,
    fundamentals: pd.DataFrame,
    tickers: Iterable[object],
    cutoff: object,
) -> pd.DataFrame:
    """Build one comparable point-in-time market/fundamental row per ticker."""
    selected = _selected_tickers(tickers)
    point = parse_cutoff(cutoff)
    performance = price_performance(prices, point)
    available = set(performance.get("instrument", pd.Series(dtype="string")))
    unknown = sorted(set(selected).difference(available))
    if unknown:
        raise ValueError(f"watchlist tickers lack eligible prices: {', '.join(unknown)}")

    market = performance.loc[performance["instrument"].isin(selected)].rename(
        columns={
            "instrument": "ticker",
            "instrument_name": "company_name",
            "available_at": "price_available_at",
            "source": "price_source",
        }
    )
    ratios = fundamental_ratios(fundamentals, point)
    if ratios.empty:
        company = pd.DataFrame({"ticker": selected})
    else:
        company = ratios.loc[ratios["company"].isin(selected)].rename(
            columns={
                "company": "ticker",
                "company_name": "filing_company_name",
                "currency": "filing_currency",
                "unit": "filing_unit",
                "available_at": "filing_available_at",
                "source": "filing_source",
            }
        )
    output = market.merge(company, on="ticker", how="left", validate="one_to_one")
    output["cutoff"] = point
    columns = [
        "ticker",
        "company_name",
        "sector",
        "latest_adjusted_close",
        "currency",
        "cumulative_return",
        "annualized_volatility",
        "revenue",
        "net_income",
        "net_margin",
        "current_ratio",
        "debt_to_equity",
        "filing_currency",
        "filing_unit",
        "latest_date",
        "price_available_at",
        "filing_available_at",
        "price_source",
        "filing_source",
        "cutoff",
    ]
    for column in columns:
        if column not in output:
            output[column] = pd.NA
    return output[columns].sort_values("ticker").reset_index(drop=True)


def normalized_performance(
    prices: pd.DataFrame,
    tickers: Iterable[object],
    cutoff: object,
) -> pd.DataFrame:
    """Index each selected adjusted-price series to 100 at its first eligible close."""
    selected = _selected_tickers(tickers)
    eligible = prices_as_of(prices, cutoff)
    available = set(eligible.get("instrument", pd.Series(dtype="string")))
    unknown = sorted(set(selected).difference(available))
    if unknown:
        raise ValueError(f"watchlist tickers lack eligible prices: {', '.join(unknown)}")
    output = eligible.loc[eligible["instrument"].isin(selected)].copy()
    output = output.sort_values(["instrument", "date"])
    first = output.groupby("instrument")["adjusted_close"].transform("first")
    output["indexed_close"] = output["adjusted_close"] / first * 100
    return output[
        ["date", "instrument", "instrument_name", "indexed_close", "available_at"]
    ].rename(columns={"instrument": "ticker", "instrument_name": "company_name"}).reset_index(drop=True)


def snapshot_hash(snapshot: pd.DataFrame) -> str:
    """Return a stable SHA-256 identity for the displayed watchlist snapshot."""
    records: list[dict[str, object]] = []
    for row in snapshot.sort_values("ticker").to_dict(orient="records"):
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
    payload = json.dumps(records, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
