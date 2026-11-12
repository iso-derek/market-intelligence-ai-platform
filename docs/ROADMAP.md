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

## Completed reviewable milestones after D2

The remaining phases are split into ten smaller review units. Each unit receives its own branch, commit, tests, documentation, and stacked draft pull request before any merge decision.

1. **D3.1 — Entity resolution:** versioned company/ticker registry, boundary-aware aliases, multi-entity mentions, and explicit resolved/ambiguous/unknown outcomes.
2. **D3.2 — Event taxonomy and linkage:** labelled event classes, company/sector links, uncertainty, and an independently evaluated deterministic baseline.
3. **D3.3 — NLP evaluation:** held-out sentiment corpus, per-class metrics, confidence intervals, overlap review, and exported model/input revisions.
4. **D4.1 — Filings corpus:** bounded local reports with document hashes, page/section/period metadata, safe parsing, and immutable manifests.
5. **D4.2 — Retrieval baselines:** lexical and embedding retrieval behind one interface with frozen relevance evaluation.
6. **D4.3 — Grounded filings QA:** cited answers, abstention, conflicting-source tests, injection resistance, and numerical consistency checks.
7. **D5.1 — Typed research workflows:** bounded Company, Macro, News, Risk, and Synthesis roles with allowlists, budgets, traces, and tested finance tools.
8. **D6.1 — Release-aware event studies:** session/timezone alignment, frozen windows, leakage controls, uncertainty, multiple-testing disclosure, and simple baselines.
9. **D6.2 — Fixed income and FX:** yield-curve, spread, and quote-direction analytics with explicit conventions and hand-checked fixtures.
10. **D7.1 — Evidence graph foundation:** provenance-backed time-aware relationships, bounded non-causal traversal, graph integrity checks, and honest local-operations boundaries.

## Product-finish milestones after D7.1

The remaining D7 acceptance criteria are split into five independently reviewable units rather than being claimed by the graph foundation.

1. **D7.2 — Graph value evaluation:** frozen graph-versus-table tasks, historical cutoffs, exactness parity, inspection-cost evidence, and an explicit negative-result interpretation.
2. **D7.3 — Reconciled research report:** deterministic report generation, claim-level citations, numeric source reconciliation, and a downloadable immutable artifact.
3. **D7.4 — Accessibility and walkthrough evidence:** labelled controls and data views, keyboard-oriented navigation review, complete user journeys, and genuine browser screenshots.
4. **D7.5 — Monitoring and recovery:** bounded operational health history, SQLite backup, verified restore, retention boundaries, and recovery instructions.
5. **D7.6 — Release-candidate validation:** fresh-install smoke evidence, secrets and capability-claim audits, deployment plan review, and an owner-controlled release checklist. No hosting is authorised by this milestone.

All five product-finish units are implemented on stacked review branches as of 7 November 2026. Their implementation does not satisfy the remaining owner-review, exact-head CI, merge, or deployment gates.

## D8 — Analyst productivity and scenario depth

D8 advances the reviewed local product without implying live coverage or deployment. Each unit remains a separate stacked review branch.

1. **D8.1 — Analyst watchlist and search:** bounded registry search, session-persistent company selection, normalized adjusted-price comparison, point-in-time fundamental comparison, and a reproducible snapshot identity.
2. **D8.2 — Deterministic stress scenarios:** explicit revenue, margin, liquidity, and leverage shocks with hand-checked arithmetic, assumptions, bounds, and no probability or forecast claim.
3. **D8.3 — Research-run history:** append-only local run artifacts, immutable identities, cutoff-aware comparison, and visible single-process persistence boundaries.

Live providers, scheduled processing, licensed news coverage, authentication, and hosting remain separate owner/infrastructure decisions rather than hidden dependencies of D8.

All three D8 units are implemented on stacked review branches as of 12 November 2026. They remain subject to exact-head CI, owner review, stack-order merge, and deployment gates.

## Definition of done

A milestone is complete only when the bounded feature works end to end, calculations/evidence are validated, meaningful tests pass, the README describes only implemented behavior, user journeys are demonstrated, limitations are visible, status is updated with exact evidence, and the owner has reviewed the pull request.
