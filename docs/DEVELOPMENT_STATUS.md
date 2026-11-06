# Development status — Market Intelligence AI Platform

**Updated:** 6 November 2026

**Phase:** D4.1 bounded filings corpus
**Status:** D1–D3.3 are stacked review branches; D4.1 is implemented on `codex/d4-1-filings-corpus`

## Baseline

- Default branch audited at `875bc6c8b8a7f6604841dcfae7616d5d247dbb1f`.
- Existing infrastructure draft PR #2 audited at `912aae44339eba881d0fc1b86f3932b5c3cbc2c2`.
- The 7 October 2026 compatibility run succeeded on Windows and Ubuntu with Python 3.12 and 3.13; the inspected Ubuntu 3.12 job reported 16 passing tests.
- This milestone is based on that infrastructure head so the launchers, CI, quick start, and run recorder are preserved rather than duplicated.
- D0 pull request #2 was squash-merged into `main` as `ced258cc2ef8838acab919a07d960928f764678a` after its exact-head four-job matrix passed.

## Completed D1 work

- Added a versioned SQLite source registry and migration path.
- Added append-only source attempts, immutable raw snapshots, article versions, and snapshot membership.
- Added idempotent imports, point-in-time evidence reconstruction, snapshot replay, and ZIP export.
- Added bounded GET-only retries and persistent source health/error reporting.
- Added native Streamlit registry controls, safe public-HTTPS registration, enabled-source selection, and snapshot downloads.
- Added migration, duplicate, revision, cutoff-invariance, outage, replay, URL-safety, fetch, and retry-policy tests.
- Documented the schema, migration, time, replay, failure, backup, and hosting boundaries.

The reviewable D1 commit is `a57649e5d2aa7cc7d9c02f856f7c8efba096641a` on draft pull request #3.

## Completed D2 work on the current branch

- Added a provider protocol and deterministic CSV provider isolated from finance calculations.
- Added a bounded three-company universe with visible currencies, calendars, source versions, and availability timestamps.
- Added raw and adjusted price views, simple cumulative returns, and sample volatility annualized with the explicit 252-session convention.
- Added revision-aware macro selection and complete-report fundamental restatement selection at historical cutoffs.
- Added peer net margin, current ratio, and debt-to-equity calculations with denominator and required-fact safeguards.
- Added a native Streamlit market lab with price, macro, company, and methodology views.
- Added hand-checked fixtures, calculation tests, and a dedicated methodology document.

The reviewable D2 commit is `2e8b058c0bdd0fd6da7491c25512b224ad9fee41` on draft pull request #4; compatibility run 42103568677 passed.

## Completed D3.1 work on the current branch

- Added a versioned deterministic company/ticker/sector registry.
- Added exact boundary-aware alias matching with longest-span precedence.
- Added multi-company resolution and explicit resolved, ambiguous, and unknown states.
- Added resolver-version and candidate identifiers to every audit row.
- Added News explorer metrics and a full resolution audit table without return-impact inference.
- Added nine focused tests covering aliases, tickers, ambiguity, unknowns, boundaries, multiple companies, case variants, versioning, and registry integrity.
- Deterministic non-UI D0–D3.1 suite: 43/43 passed locally.
- Live Streamlit browser acceptance: passed for the News explorer resolution metrics, auditable table, resolver version, and no-return-impact disclosure.

The reviewable D3.1 commit is `bf3ad8a4da1afdb28de84f63f4257a607728d024` on draft pull request #5.

## Completed D3.2 work on the current branch

- Added a transparent seven-class event taxonomy with explicit classified, ambiguous, and unknown states.
- Added matched-term, candidate, and rule-version audit fields.
- Linked event rows to every resolved company/sector without forcing ambiguous or unknown entity links.
- Added a 24-item separately labelled diagnostic with dataset hash, accuracy, macro F1, per-class metrics, confusion matrix, and prediction counts.
- Added News explorer event metrics/table and a Research evaluation diagnostic action.
- Documented taxonomy semantics, linkage boundaries, evaluation evidence, and limitations.
- Focused D3.2 suite: 8/8 passed; deterministic non-UI D0–D3.2 suite: 51/51 passed locally.
- The 24-item authored diagnostic reports accuracy 1.0 and macro F1 1.0; this is a mechanics check, not external validity evidence.
- Live Streamlit browser acceptance passed for event status metrics, conservative entity links, no-impact disclosure, and the hashed diagnostic report.

The reviewable D3.2 commit is `db5c7eb7a47fdf74bc76c948a18d0e4f5c1b7699` on draft pull request #6.

## Completed D3.3 work on the current branch

- Added a frozen balanced 30-item sentiment holdout with case IDs, source groups, review status, and split markers.
- Added per-class precision, recall, F1, support, plus the existing accuracy, macro F1, predictions, and confusion matrix.
- Added seeded nonparametric bootstrap intervals for accuracy and macro F1.
- Added case-level keyword-vocabulary overlap review and coverage reporting.
- Preserved backend and model revision identity, exact dataframe hash, and optional FinBERT isolation.
- Updated the default Research evaluation path and documented corpus, uncertainty, leakage, and interpretation boundaries.
- Focused D3.3 suite: 6/6 passed. The lexicon scored accuracy 0.8333 and macro F1 0.8375; 95% bootstrap intervals were [0.6667, 0.9667] and [0.6710, 0.9597].
- Exactly 50% of holdout headlines contain a fixed lexicon term; the report exposes every case-level overlap.
- Deterministic non-UI D0–D3.3 suite: 57/57 passed locally.
- Clean-process Streamlit browser acceptance passed for the frozen-holdout caption, per-class report, seeded intervals, overlap evidence, corpus identity, and report download.

The reviewable D3.3 commit is `9629647359f34fa43a547cf16c0ae0148a563e21` on draft pull request #7.

## Completed D4.1 work on the current branch

- Added three fictional annual reports with explicit pages, sections, fiscal periods, filing times, and availability times.
- Added an immutable corpus manifest with exact document SHA-256 values.
- Added bounded UTF-8 parsing, root-contained path checks, size/null-byte checks, hash verification, consecutive-page validation, and section-level hashes.
- Added complete-document historical cutoff filtering.
- Added a dedicated Filings corpus workspace with document and passage evidence tables.
- Added integrity, metadata, cutoff, tamper, traversal, and malformed-page tests plus a dedicated corpus methodology document.
- Focused D4.1 suite: 7/7 passed locally.
- Deterministic non-UI D0–D4.1 suite: 64/64 passed locally.
- Clean-process Streamlit browser acceptance passed for 3 verified reports / 9 pages / 18 sections and the historical cutoff that exposes only Beta and Gamma.

The reviewable D4.1 commit is `f40a037ddde5b0da18a387cb2b42b195836fd865` on its stacked draft pull request.

## D4.2 work in progress on the current branch

- Added a shared ranking contract for lexical TF-IDF and deterministic dense LSA vectors.
- Applied historical availability before fitting either retrieval baseline.
- Added eight frozen, fixture-author-reviewed query-to-passage judgements with exact corpus identity.
- Added recall@3, mean reciprocal rank, nDCG@3, and case-level result exports.
- Added the retrieval lab and explicit external-validity limitations to the Filings corpus workspace.
- Focused D4.2 suite: 7/7 passed locally.
- Frozen diagnostic results: lexical recall@3/MRR/nDCG@3 = 1.0000/1.0000/1.0000; dense LSA = 1.0000/0.9375/0.9539.
- Deterministic non-UI D0–D4.2 suite: 71/71 passed locally.
- Clean-process Streamlit browser acceptance passed for lexical and dense method selection, ranked source provenance, diagnostic metrics, and exact case-file hash.

The reviewable D4.2 commit is `ba1668a1ca1e1ff4e67c298f5d023adf1cedbf09` on its stacked draft pull request.

## D4.3 work in progress on the current branch

- Added extractive filings answers with one exact passage citation or a fixed no-citation abstention.
- Enforced entity-scoped and point-in-time evidence selection before answering.
- Preserved document, page, section, availability, and passage hash in the citation contract.
- Added a narrow instruction-like passage exclusion and tests for missing, future, and hostile evidence.
- Added ten frozen QA cases covering six supported disclosures and four abstentions.
- Focused D4.3 suite: 7/7 passed locally.
- Frozen diagnostic: 100% status accuracy, citation accuracy, expected token support, and abstention recall on the ten authored cases.
- Deterministic non-UI D0–D4.3 suite: 78/78 passed locally.
- Clean-process Streamlit browser acceptance passed for the exact warranty extract and hash-identified citation, all four diagnostics, and a dividend question that visibly abstains without a citation.

The reviewable D4.3 commit is `00b5bcb849220007d680c1e7c24bac14c1eee6aa` on its stacked draft pull request.

## D5.1 work in progress on the current branch

- Added Company, Macro, News, Risk, and Synthesis roles with fixed tool allowlists.
- Added typed facts/citations/interpretations/scenarios, step and time budgets, visible missing/error/conflict states, and canonical artifact hashes.
- Added an offline workflow inspector that deliberately preserves its missing non-synthetic News role.
- Added allowlist, budget, exception, uncited-fact, and conflicting-fact tests.
- Focused D5.1 suite: 7/7 passed locally.
- Deterministic non-UI D0–D5.1 suite: 85/85 passed locally.
- Clean-process Streamlit browser acceptance passed for five traced roles, one visible missing News role, zero silent conflicts, budgets, and the artifact SHA-256.

The reviewable D5.1 commit is `b1f97648307acdd1e3af9d08664f4f8b6d23bb97` on its stacked draft pull request.

## D6.1 work in progress on the current branch

- Added before/after-close release alignment to explicit fixture trading sessions.
- Added equal-weight peer market-adjusted abnormal returns and cumulative abnormal returns for bounded event windows.
- Applied point-in-time price availability before event-window construction.
- Added hand-checked timing, cutoff, window, benchmark, and cumulative-path tests plus visible causal-inference limitations.
- Focused D6.1 suite: 6/6 passed locally.
- Deterministic non-UI D0–D6.1 suite: 91/91 passed locally.
- Clean-process Streamlit browser acceptance passed for the before-close 6 January session, 2.54% `[-1,+1]` CAR, two-peer benchmark, window table, and causal-inference warning.

The reviewable D6.1 commit is `98348e183236ce4450d3c15dab108167c32f9180` on its stacked draft pull request.

## D6.2 work in progress on the current branch

- Added point-in-time Treasury, fictional corporate-yield, EUR/USD, and USD/NGN fixtures with explicit units and quote direction.
- Added tenor-preserving yield curves, benchmark-matched credit spreads in basis points, and base-currency FX returns with strengthening/weakening language.
- Added hand-checked cutoff, spread, return, unit, and direction tests plus a dedicated Rates & FX tab.
- Focused D6.2 suite: 6/6 passed locally.
- Deterministic non-UI D0–D6.2 suite: 97/97 passed locally.
- Clean-process Streamlit browser acceptance passed for the tenor-labelled yield curve, 140 bps Alpha 10Y spread, FX table, and BASE/QUOTE direction disclosure.

## Verification status

- Static Python compilation: passed with bundled Python 3.12.
- Focused launcher and durable-document suite: 6/6 passed with `unittest`.
- PowerShell launcher syntax: parsed successfully.
- Documentation link, capability-claim, and `git diff --check` checks: passed.
- Fresh GitHub Actions matrix: 4/4 jobs passed for milestone code commit `0b9a8d237a29bcec968a80238aed45d66002e284` on Windows and Ubuntu with Python 3.12 and 3.13 ([run 41960011053](https://github.com/iso-derek/market-intelligence-ai-platform/actions/runs/41960011053)).
- D1 persistence acceptance tests: 8/8 passed locally with Python 3.12.
- Deterministic D0/D1 suite: 25/25 passed locally with pinned dependencies.
- Live Streamlit browser acceptance reached the persistent registry and stored 15 ECB plus 12 Federal Reserve records with visible `ok` status and source-linked evidence.
- Streamlit's local `AppTest` runner stalled even for a one-line fixture in this sandbox; clean-runner CI remains the authoritative headless UI check.
- D1 exact-head GitHub Actions compatibility run 42101096333: passed at `a57649e5d2aa7cc7d9c02f856f7c8efba096641a`.
- D2 focused finance suite: 9/9 passed locally with pinned dependencies.
- Deterministic non-UI D0–D2 suite: 34/34 passed locally with a repository-scoped temporary directory.
- D2 static compilation: passed for `app.py`, `src`, and `tests`.
- Full local suite: Streamlit `AppTest` again stalled in this sandbox; deterministic non-UI tests and browser acceptance remain separate evidence, and the clean-runner matrix is authoritative.
- Live Streamlit browser acceptance at `127.0.0.1:8503`: passed for workspace navigation, adjusted-price KPIs, the 2.9-to-3.0 CPI cutoff revision, and ALP report-version 2 with visible dimensions.
- Local Streamlit browser acceptance: passed for D1, D2, D3.1, D3.2, D3.3, and D4.1 review paths.
- Optional FinBERT execution: not part of the default suite; not rerun in this milestone yet.

## Current functionality

- Synthetic demonstration and a persistent registry seeded with two official central-bank feeds.
- Immutable feed snapshots, replay exports, visible fetch history/status, and cutoff reconstruction.
- Dated CSV ingestion with explicit timestamps and URL/schema checks.
- Duplicate removal, source provenance, and content hashes.
- Keyword sentiment baseline and optional pinned FinBERT inference.
- TF-IDF headline retrieval with historical cutoff and abstention.
- Source-linked extractive briefs, citation audits, and reproducible bundles.
- Independent-label sentiment evaluation.
- Offline point-in-time market, macro, and company lab backed by educational fixtures.
- Split-aware adjusted returns, annualized volatility, revision-aware macro history, restatement-aware peer ratios, and visible data dimensions.

## Known limitations and blockers

- SQLite currently targets one local application process; multi-worker hosting, retention, and automated backup/restore are not implemented.
- D2 uses fictional offline fixtures; no live price, macro, or filing provider is integrated.
- Filings retrieval/RAG, research agents, event studies, fixed-income/FX views, and knowledge graph are not implemented.
- The 18-item diagnostic set is too small for external model-validity claims.
- Official-provider availability is external and must remain visible when it fails.
- Real screenshots must wait for an actual browser acceptance session.

## Next three priorities

1. Commit D4.1 and verify its stacked pull request in the four-job compatibility matrix.
2. Build D4.2 lexical and vector retrieval baselines with frozen relevance judgements.
3. Build D4.3 grounded filings question answering with passage-level citations and abstention.

## Remaining before a stable release

- Fresh-user installation and browser demonstration.
- Genuine screenshots and accessibility review.
- Default tests passing at the reviewed commit.
- Optional backend evidence clearly separated from default evidence.
- Reviewed deployment or verified-local-demonstration decision.
- Owner review and approval; no merge or deployment is authorised by this file.

Future sessions must verify current branch/HEAD and open PR state before relying on this snapshot. Record only work actually performed, including pass/fail/skip counts and exact commits.
