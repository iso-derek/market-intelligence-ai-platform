# Development status — Market Intelligence AI Platform

**Updated:** 5 November 2026  
**Phase:** D2 market, macro, and fundamental data
**Status:** D1 is committed for review; D2 is implemented on `codex/d2-market-macro-fundamentals`

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
- Local Streamlit browser acceptance and screenshots: pending after the full local suite.
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
- Filings RAG, research agents, event studies, fixed-income/FX views, and knowledge graph are not implemented.
- The 18-item diagnostic set is too small for external model-validity claims.
- Official-provider availability is external and must remain visible when it fails.
- Real screenshots must wait for an actual browser acceptance session.

## Next three priorities

1. Obtain clean-runner compatibility results and owner review for D1 and D2 without merging the stacked milestones prematurely.
2. Complete a browser acceptance pass of the D2 historical cutoff, CPI revision, ALP restatement, and units/timestamps.
3. Scope D3 entity resolution and independent NLP evaluation only after D2 review findings are resolved.

## Remaining before a stable release

- Fresh-user installation and browser demonstration.
- Genuine screenshots and accessibility review.
- Default tests passing at the reviewed commit.
- Optional backend evidence clearly separated from default evidence.
- Reviewed deployment or verified-local-demonstration decision.
- Owner review and approval; no merge or deployment is authorised by this file.

Future sessions must verify current branch/HEAD and open PR state before relying on this snapshot. Record only work actually performed, including pass/fail/skip counts and exact commits.
