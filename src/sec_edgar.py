"""Real company accounts from SEC EDGAR (public domain U.S. government data).

EDGAR's XBRL "company facts" API returns every figure a company has reported in
its filings, tagged with the filing date. That makes point-in-time research
possible: for any cutoff we use, for each fiscal year, the latest figure that had
been *filed* by then, so later restatements never leak into earlier views.

SEC's fair-access policy requires automated tools to identify themselves. Set
the SEC_USER_AGENT environment variable to "Your Name your.email@example.com"
(https://www.sec.gov/os/accessing-edgar-data). Nothing is requested without it.
Responses are cached for 7 days in data/cache/sec (git-ignored).
"""
from __future__ import annotations

import json
import os
import threading
import time
import urllib.request
from pathlib import Path

import pandas as pd

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
CACHE = Path(__file__).resolve().parents[1] / "data" / "cache" / "sec"
CACHE_DAYS = 7
CITATION = "U.S. Securities and Exchange Commission, EDGAR XBRL company facts (public domain)."
SOURCE_URL = "https://www.sec.gov/edgar/search/"
DEFAULT_TICKERS = ["AAPL", "MSFT", "JPM", "WMT", "XOM", "JNJ"]

# Each figure may be reported under different US-GAAP tags; the first one present wins.
CONCEPTS = {
    "revenue": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet", "RevenuesNetOfInterestExpense"],
    "net_income": ["NetIncomeLoss", "ProfitLoss"],
    "current_assets": ["AssetsCurrent"],
    "current_liabilities": ["LiabilitiesCurrent"],
    "total_debt": ["LongTermDebt", "LongTermDebtNoncurrent", "DebtInstrumentCarryingAmount"],
    "equity": ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
}
LABELS = {"revenue": "Revenue", "net_income": "Net income", "current_assets": "Current assets",
          "current_liabilities": "Current liabilities", "total_debt": "Long-term debt", "equity": "Shareholders' equity"}

_last_request = 0.0
_lock = threading.Lock()


class NotConfigured(RuntimeError):
    """Raised when SEC_USER_AGENT is not set."""


def user_agent() -> str:
    agent = os.environ.get("SEC_USER_AGENT", "").strip()
    if "@" not in agent:
        raise NotConfigured("Set SEC_USER_AGENT to your name and email (for example \"Jane Doe jane@example.com\") "
                            "so SEC knows who is requesting data. See https://www.sec.gov/os/accessing-edgar-data.")
    return agent


def _get_json(url: str, cache_name: str) -> dict:
    path = CACHE / cache_name
    if path.exists() and time.time() - path.stat().st_mtime < CACHE_DAYS * 86400:
        return json.loads(path.read_text(encoding="utf-8"))
    agent = user_agent()
    global _last_request
    with _lock:  # SEC allows at most 10 requests per second; stay well under it.
        wait = 0.2 - (time.time() - _last_request)
        if wait > 0:
            time.sleep(wait)
        request = urllib.request.Request(url, headers={"User-Agent": agent, "Accept-Encoding": "identity"})
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read()
        _last_request = time.time()
    CACHE.mkdir(parents=True, exist_ok=True)
    path.with_suffix(".part").write_bytes(body)
    path.with_suffix(".part").replace(path)
    return json.loads(body)


def ticker_index() -> dict[str, dict]:
    raw = _get_json(TICKERS_URL, "company_tickers.json")
    return {row["ticker"].upper(): {"cik": int(row["cik_str"]), "name": row["title"]} for row in raw.values()}


def annual_facts(facts: dict) -> pd.DataFrame:
    """Annual (10-K, full fiscal year) values for each figure, one row per filing of a period."""
    gaap = facts.get("facts", {}).get("us-gaap", {})
    rows = []
    for key, concepts in CONCEPTS.items():
        for concept in concepts:
            units = gaap.get(concept, {}).get("units", {}).get("USD", [])
            annual = [u for u in units if u.get("form", "").startswith("10-K") and u.get("fp") == "FY"
                      and (key not in {"revenue", "net_income"} or _is_full_year(u))]
            if annual:
                for item in annual:
                    rows.append({"metric": key, "concept": concept, "period_end": item["end"], "value": float(item["val"]),
                                 "filed": item["filed"], "form": item["form"], "accession": item.get("accn")})
                break
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame["period_end"] = pd.to_datetime(frame.period_end)
    frame["filed"] = pd.to_datetime(frame.filed)
    return frame.drop_duplicates(["metric", "period_end", "filed", "value"])


def _is_full_year(item: dict) -> bool:
    start = item.get("start")
    return start is None or 330 <= (pd.Timestamp(item["end"]) - pd.Timestamp(start)).days <= 380


def as_of(frame: pd.DataFrame, cutoff: str | pd.Timestamp) -> pd.DataFrame:
    """For each figure and period, the latest value filed on or before the cutoff."""
    if frame.empty:
        return frame
    known = frame[frame.filed <= pd.Timestamp(cutoff)]
    return known.sort_values("filed").drop_duplicates(["metric", "period_end"], keep="last")


def ratios(latest: dict[str, float]) -> dict[str, float | None]:
    def divide(a, b):
        return a / b if a is not None and b not in (None, 0) else None
    return {"net_margin": divide(latest.get("net_income"), latest.get("revenue")),
            "current_ratio": divide(latest.get("current_assets"), latest.get("current_liabilities")),
            "debt_to_equity": divide(latest.get("total_debt"), latest.get("equity"))}


def company(ticker: str, cutoff: str | pd.Timestamp) -> dict:
    index = ticker_index()
    ticker = ticker.upper()
    if ticker not in index:
        raise ValueError(f"{ticker} isn't a ticker SEC recognises.")
    info = index[ticker]
    frame = annual_facts(_get_json(FACTS_URL.format(cik=info["cik"]), f"CIK{info['cik']:010d}.json"))
    known = as_of(frame, cutoff)
    if known.empty:
        return {"ticker": ticker, "name": info["name"], "cik": info["cik"], "latest_period": None, "figures": {}, "ratios": {},
                "history": [], "restatements": 0}
    latest_period = known.period_end.max()
    latest = known[known.period_end == latest_period].set_index("metric").value.to_dict()
    filed = known[known.period_end == latest_period].filed.max()
    restated = frame[frame.filed <= pd.Timestamp(cutoff)].groupby(["metric", "period_end"]).value.nunique()
    history = (known[known.metric.isin(["revenue", "net_income"])].pivot_table(index="period_end", columns="metric", values="value")
               .sort_index().tail(6))
    return {
        "ticker": ticker, "name": info["name"].title(), "cik": info["cik"],
        "latest_period": latest_period.strftime("%Y-%m-%d"), "filed": filed.strftime("%Y-%m-%d"),
        "figures": {LABELS[k]: v for k, v in latest.items()}, "ratios": ratios(latest),
        "history": [{"period_end": stamp.strftime("%Y-%m-%d"), **{k: (None if pd.isna(v) else float(v)) for k, v in row.items()}}
                    for stamp, row in history.iterrows()],
        "restatements": int((restated > 1).sum()),
        "filings_url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={info['cik']:010d}&type=10-K",
    }
