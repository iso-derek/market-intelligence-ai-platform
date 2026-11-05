# Roadmap — Market Intelligence AI Platform

**Approved direction:** 5 November 2026. This roadmap sequences the target vision; it does not mark future features complete.

## D0 — Reproducible baseline and durable record

**Scope:** review the existing infrastructure PR, establish the product vision/roadmap/status files, reconcile README claims with the current three-area interface, improve launch instructions, and verify the default application and tests.

**Acceptance:**

- Clean installation on a supported Python version, with versions and exact commit recorded.
- Default offline suite passes on Windows and Linux for Python 3.12/3.13.
- Synthetic abstention, dated CSV evidence, malformed input, and official-feed failure paths are exercised.
- Real screenshots follow a browser acceptance session; placeholders are not accepted.
- Source and model terms are recorded.
- No claim of RAG, agents, live market coverage, or deployment.

## D1 — Persistent evidence and ingestion

Add a source registry, SQL persistence, immutable snapshot hashes, publication/retrieval/availability times, idempotent imports, source status, bounded retries, and replayable exports.

Acceptance requires duplicate/revision tests, historical-cutoff invariance, visible outages, no silent synthetic substitution, documented migrations, and reconstruction of the exact eligible evidence set.

## D2 — Market, macro, and fundamental data

Start with a bounded instrument universe, macro panel, and company set. Define adjusted/raw prices, currencies, calendars, fiscal periods, units, and source freshness. Add tested returns, volatility, statements, ratios, peers, and point-in-time joins.

Acceptance requires hand-checked fixtures, revision-aware macro history, restatement safeguards, visible units and timestamps, and provider isolation.

## D3 — NLP, entities, and independent evaluation

Preserve the keyword baseline. Evaluate optional FinBERT on an appropriate held-out corpus. Add entity/ticker resolution, event taxonomy, company/sector linkage, and explicit unknown/ambiguous states.

Acceptance requires per-class metrics, uncertainty, overlap review, labelled entity/event evaluation, exported model revision and inputs, and no return-impact inference from a mention alone.

## D4 — Filings RAG

Ingest a bounded filings/report corpus; preserve document hashes and page/section/period metadata; implement lexical and embedding baselines; add grounded QA with citations and abstention.

Acceptance requires frozen retrieval and answer evaluations, numerical consistency, semantic support review separate from link validity, conflicting-source tests, prompt-injection resistance, and comparison with the extractive baseline.

## D5 — Bounded research agents

Implement Company, Macro, News, Risk, and Synthesis roles as typed workflows. Each run has a question, as-of time, tool allowlist, time/cost limit, and trace. Finance arithmetic uses tested functions.

Acceptance requires error/missing/conflict cases, claim-level citations, separated facts/interpretation/scenarios, and evidence that multiple roles improve a single-workflow baseline.

## D6 — Event studies, fixed income, and FX

Add release-time-aware event studies before predictive modelling. Add yield curves, spread conventions, and FX quote-direction analytics.

Acceptance requires timezone/session alignment, frozen windows, no revised or post-event leakage, uncertainty and multiple-testing disclosure, and honest comparison with simple baselines.

## D7 — Knowledge graph, product finish, and operations

Add evidence-backed, time-aware graph relationships only when measured value justifies them. Finish research reports, navigation, accessibility, operational limits, monitoring, backups, and a reviewed deployment plan.

Acceptance requires provenance on every graph edge, graph-vs-nongraph evaluation, reconciled report numbers/citations, complete user walkthroughs, secrets outside Git, recovery instructions, and owner approval.

## Sequence and capacity

Recommended order: D0 → D1 → D2; D3 can follow D1; D4 depends on the evidence/company base; D5 follows evaluated retrieval; D6 follows historical data and NLP; D7 completes the broader product.

The full remaining vision is estimated at 250–420 focused engineering hours. Re-estimate after D1 and provider/model selection. The January slice should prioritise D0–D1 evidence quality while the wider portfolio's finance and FYP flagships receive validation time.

## Definition of done

A milestone is complete only when the bounded feature works end to end, calculations/evidence are validated, meaningful tests pass, the README describes only implemented behavior, user journeys are demonstrated, limitations are visible, status is updated with exact evidence, and the owner has reviewed the pull request.
