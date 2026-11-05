# Development status — Market Intelligence AI Platform

**Updated:** 5 November 2026  
**Phase:** D1 persistent evidence and ingestion
**Status:** first D1 implementation slice in progress on `codex/d1-source-registry`

## Baseline

- Default branch audited at `875bc6c8b8a7f6604841dcfae7616d5d247dbb1f`.
- Existing infrastructure draft PR #2 audited at `912aae44339eba881d0fc1b86f3932b5c3cbc2c2`.
- The 7 October 2026 compatibility run succeeded on Windows and Ubuntu with Python 3.12 and 3.13; the inspected Ubuntu 3.12 job reported 16 passing tests.
- This milestone is based on that infrastructure head so the launchers, CI, quick start, and run recorder are preserved rather than duplicated.
- D0 pull request #2 was squash-merged into `main` as `ced258cc2ef8838acab919a07d960928f764678a` after its exact-head four-job matrix passed.

## Completed D1 work on the current branch

- Added a versioned SQLite source registry and migration path.
- Added append-only source attempts, immutable raw snapshots, article versions, and snapshot membership.
- Added idempotent imports, point-in-time evidence reconstruction, snapshot replay, and ZIP export.
- Added bounded GET-only retries and persistent source health/error reporting.
- Added native Streamlit registry controls, safe public-HTTPS registration, enabled-source selection, and snapshot downloads.
- Added migration, duplicate, revision, cutoff-invariance, outage, replay, URL-safety, fetch, and retry-policy tests.
- Documented the schema, migration, time, replay, failure, backup, and hosting boundaries.

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
- D1 exact-head GitHub Actions matrix: pending a reviewable branch commit and push.
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

## Known limitations and blockers

- SQLite currently targets one local application process; multi-worker hosting, retention, and automated backup/restore are not implemented.
- Market prices, macro series, fundamentals, filings RAG, research agents, event studies, fixed-income/FX views, and knowledge graph are not implemented.
- The 18-item diagnostic set is too small for external model-validity claims.
- Official-provider availability is external and must remain visible when it fails.
- Real screenshots must wait for an actual browser acceptance session.

## Next three priorities

1. Commit and push the reviewable D1 branch, then obtain a fresh four-job compatibility matrix.
2. Confirm the post-fetch rerun and replay download on a clean browser session.
3. Open D1 for review while D2 proceeds on a separate dependent branch.

## Remaining before a stable release

- Fresh-user installation and browser demonstration.
- Genuine screenshots and accessibility review.
- Default tests passing at the reviewed commit.
- Optional backend evidence clearly separated from default evidence.
- Reviewed deployment or verified-local-demonstration decision.
- Owner review and approval; no merge or deployment is authorised by this file.

Future sessions must verify current branch/HEAD and open PR state before relying on this snapshot. Record only work actually performed, including pass/fail/skip counts and exact commits.
