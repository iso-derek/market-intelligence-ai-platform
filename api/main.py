"""JSON API for the Market Signal web app.

Every result comes from the tested modules in ``src/``. This layer picks the
point-in-time inputs, converts tables to JSON and attaches readable labels.

Run for development:  .venv/Scripts/python -m uvicorn api.main:app --reload
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import sys
import threading
from functools import lru_cache
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from data_generation import generate_news  # noqa: E402
from entities import load_entity_registry, resolution_summary, resolve_news_entities  # noqa: E402
from evaluation import evaluate_sentiment_with_uncertainty  # noqa: E402
from event_study import market_adjusted_event_study  # noqa: E402
from events import classify_news_events, evaluate_event_classifier, link_events_to_entities  # noqa: E402
from evidence import audit_claims, evidence_brief, export_bundle  # noqa: E402
from evidence_graph import evidence_paths, graph_as_of, load_evidence_graph, operations_report  # noqa: E402
from filings import filings_as_of, load_filings_corpus  # noqa: E402
from filings_qa import answer_filing_question, evaluate_filing_qa, load_qa_cases  # noqa: E402
from graph_evaluation import evaluate_graph_value, load_graph_value_cases  # noqa: E402
from ingestion import FEEDS, fetch_registered_feeds, normalise_news  # noqa: E402
from market_data import (FixtureProvider, fundamental_ratios, fundamentals_as_of, macro_as_of,  # noqa: E402
                         price_performance, prices_as_of)
from modelling import generate_market_summary, score_news  # noqa: E402
from operations import operational_health  # noqa: E402
from persistence import EvidenceStore  # noqa: E402
from rates_fx import credit_spreads, fx_performance, load_rates_fx, yield_curve  # noqa: E402
from research_history import comparison_display_frame, compare_workflow_runs, save_workflow_run, workflow_run_history  # noqa: E402
from research_report import build_reconciled_report, export_report_bundle  # noqa: E402
from retrieval import evaluate_retriever, load_relevance_cases, rank_passages  # noqa: E402
from scenario_analysis import SCENARIO_PRESETS, ScenarioAssumptions, scenario_hash, stress_watchlist  # noqa: E402
from watchlist import company_universe, normalized_performance, search_companies, snapshot_hash, watchlist_snapshot  # noqa: E402
from workflow_dashboard import COMPANY_FACTS, RISK_IDS, _company_facts, _evidence_catalog, _macro_fact  # noqa: E402
from workflows import WorkflowRequest, make_demo_tools, run_workflow  # noqa: E402

FIXTURES = ROOT / "data" / "fixtures"
EVALUATION = ROOT / "data" / "evaluation"
DB_PATH = Path(os.environ.get("MARKET_INTELLIGENCE_DB", ROOT / "data" / "runtime" / "evidence.db"))
RUNS_ROOT = Path(os.environ.get("MARKET_INTELLIGENCE_RUNS", ROOT / "runs"))

# Historical views shared by the market, watchlist and workflow workspaces.
VIEWS = {
    "before-revisions": {"label": "31 Jan 2026 · before revisions", "cutoff": "2026-01-31T23:59:59Z"},
    "revised": {"label": "1 Mar 2026 · revised history", "cutoff": "2026-03-01T23:59:59Z"},
}
FILING_VIEWS = {
    "beta-only": {"label": "23 Jan 2026 · Beta only", "cutoff": "2026-01-23T23:59:59Z"},
    "beta-gamma": {"label": "1 Feb 2026 · Beta and Gamma", "cutoff": "2026-02-01T23:59:59Z"},
    "all": {"label": "1 Mar 2026 · all reports", "cutoff": "2026-03-01T23:59:59Z"},
}
GRAPH_VIEWS = {
    "feb": {"label": "1 Feb 2026", "cutoff": "2026-02-01T23:59:59Z"},
    "mar": {"label": "1 Mar 2026", "cutoff": "2026-03-01T23:59:59Z"},
}
COMPANY_NAMES = {"ALP": "Alpha Industries", "BET": "Beta Retail", "GAM": "Gamma Software"}
METRIC_NAMES = {
    "revenue": "Revenue", "net_income": "Net income", "current_assets": "Current assets",
    "current_liabilities": "Current liabilities", "total_debt": "Total debt", "shareholders_equity": "Shareholders' equity",
    "cpi": "Consumer price inflation",
}
TOPIC_NAMES = {"interest rates": "Interest rates"}

app = FastAPI(title="Market Signal API", version="1.0.0")
_lock = threading.RLock()
_uploads: dict[str, pd.DataFrame] = {}


# ---------------------------------------------------------------- helpers
def records(frame: pd.DataFrame) -> list[dict]:
    return json.loads(frame.to_json(orient="records", date_format="iso", default_handler=str))


def num(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if np.isfinite(value) else None


def iso(value) -> str | None:
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return None
    return pd.Timestamp(value).isoformat()


def risk_flags(value) -> list[str]:
    """Split a stored risk-flag string; empty markers such as 'None' mean no flags."""
    if not isinstance(value, str):
        return []
    return [flag.strip() for flag in value.split(",") if flag.strip() and flag.strip().lower() not in {"none", "nan"}]


def humanize(text: str) -> str:
    text = str(text).replace("_", " ").strip()
    return text[:1].upper() + text[1:]


def view(key: str, table: dict) -> str:
    if key not in table:
        raise HTTPException(400, "Choose one of the listed historical views.")
    return table[key]["cutoff"]


def options(table: dict) -> list[dict]:
    return [{"key": key, "label": value["label"]} for key, value in table.items()]


def guarded(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@lru_cache(maxsize=1)
def market_bundle():
    provider = FixtureProvider(FIXTURES)
    return provider.prices(), provider.macro(), provider.fundamentals(), load_rates_fx(FIXTURES / "rates_fx.csv")


@lru_cache(maxsize=1)
def registry():
    return load_entity_registry(FIXTURES / "entity_registry.csv")


@lru_cache(maxsize=1)
def store() -> EvidenceStore:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    evidence = EvidenceStore(str(DB_PATH))
    evidence.ensure_sources(FEEDS)
    return evidence


# ---------------------------------------------------------------- news evidence
@lru_cache(maxsize=1)
def demo_news() -> pd.DataFrame:
    raw = generate_news(120)
    raw["source"] = "Synthetic demonstration"
    raw["synthetic"] = True
    return score_news(normalise_news(raw))


def news_frame(source: str) -> pd.DataFrame:
    if source == "demo":
        return demo_news()
    if source == "official":
        with _lock:
            frame = store().eligible_evidence()
        return score_news(frame) if not frame.empty else frame
    if source in _uploads:
        return _uploads[source]
    raise HTTPException(404, "That uploaded file is no longer loaded. Please upload it again.")


@app.get("/api/news")
def news(source: str = "demo", search: str = "", sentiment: str = "", ticker: str = "", limit: int = Query(40, ge=1, le=500)):
    frame = news_frame(source)
    if frame.empty:
        return {"source": source, "empty": True, "synthetic": False, "kpis": None, "headlines": [], "total": 0}
    resolutions = resolve_news_entities(frame, registry())
    events = link_events_to_entities(classify_news_events(frame), resolutions)
    view_frame = frame
    if search:
        view_frame = view_frame[view_frame.headline.str.contains(search, case=False, regex=False)]
    if sentiment:
        view_frame = view_frame[view_frame.sentiment_label.eq(sentiment)]
    if ticker and "ticker" in view_frame:
        view_frame = view_frame[view_frame.ticker.eq(ticker)]
    view_frame = view_frame.sort_values("published_at", ascending=False)
    monthly = (frame.assign(month=pd.to_datetime(frame.published_at, utc=True).dt.strftime("%Y-%m"))
               .groupby(["month", "sentiment_label"]).size().unstack(fill_value=0).reset_index())
    companies = (frame.groupby("company").agg(headlines=("article_id", "count"), tone=("sentiment_score", "mean"))
                 .sort_values("headlines", ascending=False).head(8).reset_index()) if "company" in frame else pd.DataFrame()
    event_counts = events[events.event_status.eq("classified")].event_type.value_counts()
    return {
        "source": source,
        "empty": False,
        "synthetic": bool(frame.get("synthetic", pd.Series([False])).fillna(False).astype(bool).any()),
        "summary": generate_market_summary(frame),
        "kpis": {"headlines": int(len(frame)), "sources": int(frame.source.nunique()),
                 "negative": int(frame.sentiment_label.eq("Negative").sum()),
                 "positive": int(frame.sentiment_label.eq("Positive").sum()),
                 "risk_flagged": int(frame.risk_flags.map(lambda value: bool(risk_flags(value))).sum()) if "risk_flags" in frame else 0,
                 "average_tone": num(frame.sentiment_score.mean())},
        "monthly": records(monthly),
        "companies": records(companies),
        "tickers": sorted(frame.ticker.dropna().unique().tolist()) if "ticker" in frame else [],
        "entities": {**resolution_summary(resolutions)},
        "events": {"classified": int(events.event_status.eq("classified").sum()),
                   "ambiguous": int(events.event_status.eq("ambiguous").sum()),
                   "unknown": int(events.event_status.eq("unknown").sum()),
                   "types": [{"type": humanize(k), "count": int(v)} for k, v in event_counts.items()]},
        "total": int(len(view_frame)),
        "headlines": [{
            "id": row.article_id, "headline": row.headline, "source": row.source, "url": row.url or None,
            "published_at": iso(row.published_at), "available_at": iso(row.available_at),
            "company": getattr(row, "company", None), "ticker": getattr(row, "ticker", None),
            "sentiment": row.sentiment_label, "score": num(row.sentiment_score),
            "risk": risk_flags(row.risk_flags),
        } for row in view_frame.head(limit).itertuples(index=False)],
    }


class BriefRequest(BaseModel):
    source: str = "demo"
    query: str = Field("", max_length=300)
    cutoff: str | None = None


@app.post("/api/news/brief")
def brief(request: BriefRequest):
    frame = news_frame(request.source)
    if frame.empty:
        return {"abstained": True, "reason": "No evidence is loaded yet.", "claims": [], "audit": []}
    result = guarded(evidence_brief, frame, request.query, request.cutoff or pd.Timestamp.now(tz="UTC").isoformat())
    audit = audit_claims(result["claims"], frame)
    return {**{k: v for k, v in result.items() if k != "claims"},
            "claims": [{**claim, "published_at": iso(claim.get("published_at"))} for claim in result["claims"]],
            "audit": records(audit)}


class UploadRequest(BaseModel):
    csv: str = Field(..., max_length=20_000_000)


@app.post("/api/news/upload")
def upload_news(request: UploadRequest):
    try:
        frame = score_news(normalise_news(pd.read_csv(io.StringIO(request.csv))))
    except (ValueError, KeyError, pd.errors.ParserError) as exc:
        raise HTTPException(422, f"The file couldn't be read: {exc}") from exc
    key = "upload-" + hashlib.sha256(request.csv.encode()).hexdigest()[:12]
    _uploads[key] = frame
    return {"source": key, "headlines": int(len(frame))}


@app.get("/api/news/download")
def download_news(source: str = "demo", query: str = ""):
    frame = news_frame(source)
    result = evidence_brief(frame, query, pd.Timestamp.now(tz="UTC").isoformat())
    return Response(export_bundle(frame, result, {"sentiment_model": "Keyword baseline"}), media_type="application/zip",
                    headers={"Content-Disposition": 'attachment; filename="market_research.zip"'})


@app.get("/api/news/evaluation")
def news_evaluation():
    holdout = pd.read_csv(EVALUATION / "sentiment_holdout.csv")
    report = evaluate_sentiment_with_uncertainty(holdout, "lexicon")
    events = evaluate_event_classifier(pd.read_csv(EVALUATION / "event_taxonomy_cases.csv"))
    return json.loads(json.dumps({"sentiment": report, "events": events}, default=str))


# ---------------------------------------------------------------- official sources
@app.get("/api/sources")
def sources():
    with _lock:
        table = store().list_sources()
        snapshots = store().snapshots()
    return {"sources": records(table[["source_id", "name", "feed_url", "enabled", "last_status", "last_checked_at", "last_error"]]),
            "snapshots": int(len(snapshots)), "schema_version": store().schema_version()}


class SourceToggle(BaseModel):
    enabled: bool


@app.patch("/api/sources/{source_id}")
def toggle_source(source_id: str, body: SourceToggle):
    with _lock:
        guarded(store().set_enabled, source_id, body.enabled)
    return sources()


class NewSource(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    url: str = Field(..., min_length=8, max_length=500)


@app.post("/api/sources")
def add_source(body: NewSource):
    with _lock:
        try:
            store().register_source(body.name, body.url)
        except (ValueError, TypeError) as exc:
            raise HTTPException(422, str(exc)) from exc
    return sources()


@app.post("/api/sources/fetch")
def fetch_sources():
    with _lock:
        _, diagnostics = fetch_registered_feeds(store())
    return {"diagnostics": json.loads(json.dumps(diagnostics, default=str)), **sources()}


# ---------------------------------------------------------------- markets
@app.get("/api/markets")
def markets(view_key: str = Query("revised", alias="view"), instrument: str = "ALP"):
    cutoff = view(view_key, VIEWS)
    prices, macro, fundamentals, rates = market_bundle()
    performance = price_performance(prices, cutoff)
    if instrument not in set(performance.instrument):
        raise HTTPException(400, "Choose one of the listed companies.")
    selected = performance.set_index("instrument").loc[instrument]
    available_prices = prices_as_of(prices, cutoff)
    macro_rows = macro_as_of(macro, cutoff).sort_values("observation_date")
    latest_macro = macro_rows.drop_duplicates("series_id", keep="last")
    peers = fundamental_ratios(fundamentals, cutoff)
    facts = fundamentals_as_of(fundamentals, cutoff)
    focus = facts[facts.company.eq(instrument)]
    curve, spreads, fx = yield_curve(rates, cutoff), credit_spreads(rates, cutoff), fx_performance(rates, cutoff)
    return {
        "views": options(VIEWS), "view": view_key, "cutoff": cutoff,
        "companies": [{"key": r.instrument, "label": r.instrument_name} for r in performance.itertuples(index=False)],
        "instrument": instrument,
        "headline": {"name": selected.instrument_name, "close": num(selected.latest_adjusted_close), "currency": selected.currency,
                     "return": num(selected.cumulative_return), "volatility": num(selected.annualized_volatility),
                     "exchange": selected.calendar, "latest": iso(selected.latest_date)},
        "prices": [{"date": iso(r.date), "raw": num(r.raw_close), "adjusted": num(r.adjusted_close)}
                   for r in available_prices[available_prices.instrument.eq(instrument)].itertuples(index=False)],
        "universe": [{"ticker": r.instrument, "name": r.instrument_name, "close": num(r.latest_adjusted_close), "currency": r.currency,
                      "return": num(r.cumulative_return), "volatility": num(r.annualized_volatility), "days": int(r.observations)}
                     for r in performance.itertuples(index=False)],
        "macro": {"latest": [{"id": r.series_id, "name": r.series_name, "value": num(r.value), "unit": r.unit,
                              "period": iso(r.observation_date), "available_at": iso(r.available_at)} for r in latest_macro.itertuples(index=False)],
                  "history": [{"id": r.series_id, "name": r.series_name, "period": iso(r.observation_date), "value": num(r.value),
                               "unit": r.unit, "released": iso(r.release_at), "vintage": iso(r.vintage_at), "available_at": iso(r.available_at)}
                              for r in macro_rows.itertuples(index=False)]},
        "peers": [{"ticker": r.company, "name": r.company_name, "sector": r.sector, "revenue": num(r.revenue), "net_income": num(r.net_income),
                   "net_margin": num(r.net_margin), "current_ratio": num(r.current_ratio), "debt_to_equity": num(r.debt_to_equity),
                   "currency": r.currency, "unit": r.unit, "version": int(r.report_version), "available_at": iso(r.available_at)}
                  for r in peers.itertuples(index=False)],
        "facts": [{"metric": METRIC_NAMES.get(r.metric, humanize(r.metric)), "value": num(r.value), "currency": r.currency, "unit": r.unit,
                   "version": int(r.report_version), "filed": iso(r.filed_at)} for r in focus.itertuples(index=False)],
        "rates": {"curve": [{"name": r.instrument, "tenor": r.tenor, "value": num(r.value)} for r in curve.itertuples(index=False)],
                  "spreads": [{"name": r.instrument, "tenor": r.tenor, "yield": num(r.yield_percent), "benchmark": r.benchmark,
                               "benchmark_yield": num(r.benchmark_yield_percent), "spread_bps": num(r.spread_bps)} for r in spreads.itertuples(index=False)],
                  "fx": [{"pair": r.instrument, "unit": r.unit, "first": num(r.first_value), "latest": num(r.latest_value),
                          "return": num(r.base_return), "meaning": r.interpretation} for r in fx.itertuples(index=False)]},
    }


@app.get("/api/markets/event")
def market_event(instrument: str = "ALP", release: Literal["2026-01-06T14:00:00Z", "2026-01-05T22:00:00Z"] = "2026-01-06T14:00:00Z",
                 view_key: str = Query("revised", alias="view")):
    prices, *_ = market_bundle()
    summary, window = guarded(market_adjusted_event_study, prices, instrument, release, view(view_key, VIEWS), 1, 1)
    return {"session": iso(summary["event_session"]), "car": num(summary["car"]), "peers": int(summary["peer_count"]),
            "window": [{"day": int(r.relative_day), "date": iso(r.date), "instrument": num(r.instrument_return),
                        "benchmark": num(r.benchmark_return), "abnormal": num(r.abnormal_return),
                        "cumulative": num(r.cumulative_abnormal_return)} for r in window.itertuples(index=False)]}


# ---------------------------------------------------------------- watchlist
@app.get("/api/watchlist")
def watchlist(view_key: str = Query("revised", alias="view"), tickers: str = "ALP,BET,GAM", q: str = "", sectors: str = ""):
    cutoff = view(view_key, VIEWS)
    prices, _, fundamentals, _ = market_bundle()
    universe = company_universe(registry(), prices, cutoff)
    chosen = [t for t in dict.fromkeys(t.strip().upper() for t in tickers.split(",") if t.strip()) if t in set(universe.ticker)]
    matches = search_companies(universe, q, [s for s in sectors.split(",") if s])
    result = {
        "views": options(VIEWS), "view": view_key,
        "universe": [{"ticker": r.ticker, "name": r.canonical_name, "sector": r.sector, "aliases": str(r.aliases).replace("|", ", ")}
                     for r in universe.itertuples(index=False)],
        "sectors": sorted(universe.sector.unique().tolist()),
        "matches": [r.ticker for r in matches.itertuples(index=False)],
        "selected": chosen,
        "presets": {name: vars(preset) for name, preset in SCENARIO_PRESETS.items()},
    }
    if not chosen:
        return {**result, "snapshot": [], "indexed": [], "identity": None}
    snapshot = watchlist_snapshot(prices, fundamentals, chosen, cutoff)
    indexed = normalized_performance(prices, chosen, cutoff)
    pivot = indexed.pivot_table(index="date", columns="ticker", values="indexed_close").reset_index()
    return {**result, "identity": snapshot_hash(snapshot),
            "snapshot": [{"ticker": r.ticker, "name": r.company_name, "sector": r.sector, "close": num(r.latest_adjusted_close),
                          "currency": r.currency, "return": num(r.cumulative_return), "volatility": num(r.annualized_volatility),
                          "revenue": num(r.revenue), "net_income": num(r.net_income), "net_margin": num(r.net_margin),
                          "current_ratio": num(r.current_ratio), "debt_to_equity": num(r.debt_to_equity),
                          "unit": f"{r.filing_currency} {r.filing_unit}", "price_source": r.price_source, "filing_source": r.filing_source,
                          "price_available_at": iso(r.price_available_at), "filing_available_at": iso(r.filing_available_at)}
                         for r in snapshot.itertuples(index=False)],
            "indexed": [{"date": iso(row["date"]), **{t: num(row.get(t)) for t in chosen}} for _, row in pivot.iterrows()]}


@app.get("/api/watchlist/stress")
def watchlist_stress(view_key: str = Query("revised", alias="view"), tickers: str = "ALP,BET,GAM",
                     revenue: float = Query(-0.1, ge=-0.5, le=0.5), margin_bps: int = Query(-300, ge=-2000, le=2000),
                     assets: float = Query(-0.1, ge=-0.5, le=0.5), liabilities: float = Query(0.1, ge=-0.5, le=0.5),
                     debt: float = Query(0.2, ge=-0.5, le=1), equity: float = Query(-0.1, ge=-0.5, le=0.5)):
    cutoff = view(view_key, VIEWS)
    prices, _, fundamentals, _ = market_bundle()
    chosen = [t for t in tickers.split(",") if t]
    if not chosen:
        raise HTTPException(400, "Pick at least one company.")
    snapshot = guarded(watchlist_snapshot, prices, fundamentals, chosen, cutoff)
    assumptions = ScenarioAssumptions(revenue_shock=revenue, margin_shock_bps=margin_bps, current_assets_shock=assets,
                                      current_liabilities_shock=liabilities, debt_shock=debt, equity_shock=equity)
    stressed = guarded(stress_watchlist, snapshot, assumptions)
    return {"identity": scenario_hash(stressed, assumptions), "unit": f"{stressed.filing_currency.iloc[0]} {stressed.filing_unit.iloc[0]}",
            "rows": [{"ticker": r.ticker, "name": r.company_name, "revenue": num(r.revenue), "stressed_revenue": num(r.stressed_revenue),
                      "net_margin": num(r.net_margin), "stressed_net_margin": num(r.stressed_net_margin),
                      "net_income": num(r.net_income), "stressed_net_income": num(r.stressed_net_income), "change": num(r.net_income_change),
                      "current_ratio": num(r.current_ratio), "stressed_current_ratio": num(r.stressed_current_ratio),
                      "debt_to_equity": num(r.debt_to_equity), "stressed_debt_to_equity": num(r.stressed_debt_to_equity)}
                     for r in stressed.itertuples(index=False)]}


# ---------------------------------------------------------------- filings
@lru_cache(maxsize=1)
def corpus():
    return load_filings_corpus(ROOT / "data" / "filings")


def _passage(row) -> dict:
    return {"id": row.passage_id, "document": row.document_id, "company": row.company, "page": int(row.page),
            "section": str(row.section).replace("�", "–"), "text": row.text, "available_at": iso(row.available_at),
            "hash": row.text_sha256}


@app.get("/api/filings")
def filings(view_key: str = Query("all", alias="view")):
    documents, passages = corpus()
    eligible_docs, eligible_passages = filings_as_of(documents, passages, view(view_key, FILING_VIEWS))
    return {"views": options(FILING_VIEWS), "view": view_key,
            "documents": [{"id": r.document_id, "company": r.company, "ticker": r.ticker, "form": r.form, "period_end": iso(r.period_end),
                           "filed": iso(r.filed_at), "available_at": iso(r.available_at), "pages": int(r.pages), "sections": int(r.sections),
                           "verified": bool(r.hash_verified), "hash": r.sha256}
                          for r in eligible_docs.itertuples(index=False)],
            "passages": [_passage(r) for r in eligible_passages.itertuples(index=False)]}


@app.get("/api/filings/search")
def filings_search(q: str, method: Literal["lexical", "dense_lsa"] = "lexical", top_k: int = Query(3, ge=1, le=8),
                   view_key: str = Query("all", alias="view")):
    documents, passages = corpus()
    _, eligible = filings_as_of(documents, passages, view(view_key, FILING_VIEWS))
    if not q.strip() or eligible.empty:
        return {"results": []}
    ranked = guarded(rank_passages, eligible, q, method=method, top_k=top_k)
    return {"results": [{**_passage(r), "rank": int(r.rank), "score": num(r.score)} for r in ranked.itertuples(index=False)]}


@app.get("/api/filings/answer")
def filings_answer(q: str, view_key: str = Query("all", alias="view")):
    _, passages = corpus()
    result = guarded(answer_filing_question, passages, q, view(view_key, FILING_VIEWS))
    return json.loads(json.dumps({**result, "citations": [{**c, "section": str(c.get("section", "")).replace("�", "–")}
                                                          for c in result.get("citations", [])]}, default=str))


@app.get("/api/filings/evaluation")
def filings_evaluation():
    _, passages = corpus()
    cases = load_relevance_cases(EVALUATION / "filings_relevance_cases.csv")
    retrieval = [evaluate_retriever(passages, cases, method, top_k=3)[0] for method in ("lexical", "dense_lsa")]
    qa_summary, qa_details = evaluate_filing_qa(passages, load_qa_cases(EVALUATION / "filings_qa_cases.csv"))
    return json.loads(json.dumps({"retrieval": retrieval, "qa": qa_summary,
                                  "qa_cases": records(qa_details[["question", "expected_status", "actual_status", "status_correct", "citation_correct"]])},
                                 default=str))


# ---------------------------------------------------------------- research workflow
def _workflow(company: str, view_key: str, question: str, max_seconds: float):
    if company not in COMPANY_FACTS:
        raise HTTPException(400, "Choose one of the listed companies.")
    cutoff = view(view_key, VIEWS)
    label = "31 January" if view_key == "before-revisions" else "1 March"
    facts, macro_fact = _company_facts(company, label), _macro_fact(label)
    request = WorkflowRequest(question or f"What is the evidence-backed outlook and risk context for {company}?", cutoff, company,
                              max_steps=5, max_seconds=float(max_seconds))
    artifact = run_workflow(request, make_demo_tools(facts, [macro_fact], [{"evidence_id": RISK_IDS[company], "kind": "filing_risk_factor"}]))
    report = build_reconciled_report(artifact, _evidence_catalog(company, facts, macro_fact, label))
    return artifact, report


@app.get("/api/workflow")
def workflow(company: str = "ALP", view_key: str = Query("revised", alias="view"), question: str = "", max_seconds: float = Query(5, ge=1, le=10)):
    artifact, report = _workflow(company, view_key, question, max_seconds)
    return json.loads(json.dumps({
        "views": options(VIEWS), "companies": [{"key": k, "label": v} for k, v in COMPANY_NAMES.items()],
        "status": artifact["status"], "budget": artifact["budget"], "artifact_hash": artifact["artifact_sha256"],
        "question": artifact["request"]["question"] if isinstance(artifact.get("request"), dict) else question,
        "trace": [{"step": t["step"], "role": t["role"], "tool": humanize(t["tool"]), "status": t["status"], "message": t.get("message", ""),
                   "facts": [{**f, "label": METRIC_NAMES.get(str(f.get("fact_key")), humanize(f.get("fact_key", "")))} for f in t.get("facts", [])],
                   "citations": len(t.get("citations", []))} for t in artifact["trace"]],
        "report": {"claims": [{**claim, "label": METRIC_NAMES.get(str(claim.get("fact_key")), humanize(claim.get("fact_key", "")))}
                              for claim in report["claims"]],
                   "reconciliation": report["reconciliation"], "hash": report["report_sha256"],
                   "limitations": report["limitations"]},
    }, default=str))


class SaveRun(BaseModel):
    company: str = "ALP"
    view: str = "revised"
    question: str = ""
    max_seconds: float = Field(5, ge=1, le=10)


@app.post("/api/workflow/runs")
def save_run(body: SaveRun):
    artifact, report = _workflow(body.company, body.view, body.question, body.max_seconds)
    with _lock:
        try:
            folder, created = save_workflow_run(RUNS_ROOT, artifact, report)
        except (OSError, ValueError) as exc:
            raise HTTPException(500, f"The run couldn't be saved: {exc}") from exc
    return {"run": folder.name, "created": created}


@app.get("/api/workflow/runs")
def runs():
    try:
        history = workflow_run_history(RUNS_ROOT)
    except (OSError, ValueError) as exc:
        raise HTTPException(500, f"Stored runs failed their integrity check: {exc}") from exc
    if history.empty:
        return {"runs": []}
    return {"runs": [{"id": r.run_id, "recorded_at": iso(r.recorded_at), "as_of": iso(r.research_as_of), "company": COMPANY_NAMES.get(r.company, r.company),
                      "status": r.status} for r in history.itertuples(index=False)]}


@app.get("/api/workflow/compare")
def compare(base: str, target: str):
    history = workflow_run_history(RUNS_ROOT)
    folders = dict(zip(history.run_id, history.folder)) if not history.empty else {}
    if base not in folders or target not in folders:
        raise HTTPException(404, "Pick two saved runs.")
    comparison = compare_workflow_runs(folders[base], folders[target])
    table = comparison_display_frame(comparison["metrics"])
    return json.loads(json.dumps({"rows": records(table), "cutoff_relation": comparison["cutoff_relation"],
                                  "same_company": comparison["same_company"], "limitations": comparison["limitations"]}, default=str))


@app.get("/api/workflow/report")
def report_download(company: str = "ALP", view_key: str = Query("revised", alias="view"), question: str = ""):
    _, report = _workflow(company, view_key, question, 5)
    return Response(export_report_bundle(report), media_type="application/zip",
                    headers={"Content-Disposition": f'attachment; filename="{company.lower()}-reconciled-report.zip"'})


# ---------------------------------------------------------------- evidence graph & operations
@app.get("/api/graph")
def graph(view_key: str = Query("mar", alias="view")):
    nodes, edges, graph_hash = load_evidence_graph(FIXTURES / "evidence_graph_nodes.csv", FIXTURES / "evidence_graph_edges.csv")
    eligible_nodes, eligible_edges = graph_as_of(nodes, edges, view(view_key, GRAPH_VIEWS))
    paths = evidence_paths(eligible_edges, "company:ALP", 4) if not eligible_edges.empty else pd.DataFrame()
    cases, case_hash = load_graph_value_cases(EVALUATION / "graph_value_cases.csv")
    evaluation = evaluate_graph_value(nodes, edges, cases, case_hash)
    return json.loads(json.dumps({
        "views": options(GRAPH_VIEWS), "view": view_key, "hash": graph_hash,
        "nodes": [{"id": r.node_id, "type": humanize(r.node_type), "label": r.label, "available_at": iso(r.available_at)} for r in eligible_nodes.itertuples(index=False)],
        "edges": [{"id": r.edge_id, "from": r.source_id, "to": r.target_id, "relationship": humanize(r.relationship), "available_at": iso(r.available_at)}
                  for r in eligible_edges.itertuples(index=False)],
        "paths": records(paths) if not paths.empty else [],
        "evaluation": {k: v for k, v in evaluation.items() if k != "results"},
    }, default=str))


@app.get("/api/operations")
def operations():
    nodes, edges, graph_hash = load_evidence_graph(FIXTURES / "evidence_graph_nodes.csv", FIXTURES / "evidence_graph_edges.csv")
    health = operational_health(DB_PATH)
    return json.loads(json.dumps({"health": health, "report": operations_report(ROOT, graph_hash)}, default=str))


@app.get("/api/health")
def api_health():
    return {"status": "ok"}


WEB_DIST = ROOT / "web" / "dist"
if WEB_DIST.exists():
    app.mount("/assets", StaticFiles(directory=WEB_DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        candidate = (WEB_DIST / path).resolve()
        if path and candidate.is_file() and WEB_DIST.resolve() in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(WEB_DIST / "index.html")
