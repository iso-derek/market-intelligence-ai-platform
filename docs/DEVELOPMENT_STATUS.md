# Development status — Market Intelligence AI Platform

**Updated:** 5 November 2026  
**Phase:** D0 reproducible baseline and durable record  
**Status:** local readiness checks and fresh compatibility matrix passed

## Baseline

- Default branch audited at `875bc6c8b8a7f6604841dcfae7616d5d247dbb1f`.
- Existing infrastructure draft PR #2 audited at `912aae44339eba881d0fc1b86f3932b5c3cbc2c2`.
- The 7 October 2026 compatibility run succeeded on Windows and Ubuntu with Python 3.12 and 3.13; the inspected Ubuntu 3.12 job reported 16 passing tests.
- This milestone is based on that infrastructure head so the launchers, CI, quick start, and run recorder are preserved rather than duplicated.

## Completed in the current milestone branch

- Rewrote README claims around the implemented evidence, ingestion, sentiment, and evaluation workflow.
- Added complete target vision and phased roadmap documents.
- Added this durable development-status record.
- Added a detailed source/model provenance and licensing record.
- Replaced the generic quick start with Market Intelligence user journeys and troubleshooting.
- Updated Windows launchers to fall back from Python 3.13 to 3.12 and pass command-line arguments through.

## Verification status

- Static Python compilation: passed with bundled Python 3.12.
- Focused launcher and durable-document suite: 6/6 passed with `unittest`.
- PowerShell launcher syntax: parsed successfully.
- Documentation link, capability-claim, and `git diff --check` checks: passed.
- Fresh GitHub Actions matrix: 4/4 jobs passed for milestone code commit `0b9a8d237a29bcec968a80238aed45d66002e284` on Windows and Ubuntu with Python 3.12 and 3.13 ([run 41960011053](https://github.com/iso-derek/market-intelligence-ai-platform/actions/runs/41960011053)).
- Local dependency installation: attempted with bundled Python 3.12, but the environment reset PyPI downloads. This is an environment/network result, not an application test failure.
- Local Streamlit browser acceptance and screenshots: pending a successful dependency installation.
- Optional FinBERT execution: not part of the default suite; not rerun in this milestone yet.

## Current functionality

- Synthetic demonstration and two on-demand official central-bank feeds.
- Dated CSV ingestion with explicit timestamps and URL/schema checks.
- Duplicate removal, source provenance, and content hashes.
- Keyword sentiment baseline and optional pinned FinBERT inference.
- TF-IDF headline retrieval with historical cutoff and abstention.
- Source-linked extractive briefs, citation audits, and reproducible bundles.
- Independent-label sentiment evaluation.

## Known limitations and blockers

- There is no persistent source registry yet; this is D1.
- Market prices, macro series, fundamentals, filings RAG, research agents, event studies, fixed-income/FX views, and knowledge graph are not implemented.
- The 18-item diagnostic set is too small for external model-validity claims.
- Official-provider availability is external and must remain visible when it fails.
- Real screenshots must wait for an actual browser acceptance session.

## Next three priorities

1. Complete local dashboard acceptance and capture genuine screenshots when dependency installation is available.
2. Review D0 pull request #2 and decide whether the baseline is ready to merge.
3. Begin D1 only after D0 review and scope confirmation.

## Remaining before a stable release

- Fresh-user installation and browser demonstration.
- Genuine screenshots and accessibility review.
- Default tests passing at the reviewed commit.
- Optional backend evidence clearly separated from default evidence.
- Reviewed deployment or verified-local-demonstration decision.
- Owner review and approval; no merge or deployment is authorised by this file.

Future sessions must verify current branch/HEAD and open PR state before relying on this snapshot. Record only work actually performed, including pass/fail/skip counts and exact commits.
