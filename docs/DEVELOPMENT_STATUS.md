# Development status — Market Intelligence AI Platform

**Updated:** 12 November 2026

**Phase:** D8 analyst productivity and scenario depth
**Status:** D1–D8.1 are implemented as stacked review branches; D8.2 deterministic stress scenarios are implemented on `codex/d8-2-deterministic-stress-scenarios`

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

The reviewable D6.2 commit is `6ed7f5860d437ef54e5df2aae6527c4d2fa08ab5` on its stacked draft pull request.

## Completed D7.1 work

- Added a point-in-time provenance graph with unique IDs, evidence URIs, availability timestamps, and a canonical hash.
- Added dangling-reference, relationship allowlist, non-causal language, bounded-path, and cycle safeguards.
- Added an operations report that verifies durable files and honestly labels the current target as a verified local demo rather than hosted deployment.
- Focused D7.1 suite: 6/6 passed locally.
- Deterministic non-UI D0–D7.1 suite: 103/103 passed locally.
- Clean-process Streamlit browser acceptance passed for 6 nodes, 5 edges, zero dangling links, graph hash, bounded provenance paths, required-file health, and the `verified_local_demo_not_hosted` boundary.

The reviewable D7.1 commit is `43938a9d` on stacked draft pull request #14. A later cross-platform fixture fix was propagated through the stack; the D7.1 branch head before D7.2 was `53a53a42e2e884af61ed238c0a82739d8f14262d`.

## Completed D7.2 work on the current branch

- Added five frozen graph-versus-table lookup cases with an exact case-file SHA-256.
- Applied identical historical availability cutoffs and hop bounds to both methods.
- Compared exact found state and relationship sequences rather than assuming the graph is superior.
- Added deterministic operation counts for adjacency traversal and repeated table scans.
- Both methods are exact on the authored fixture; the graph's measured advantage is reduced repeated row inspection and explicit multi-hop provenance, not better answer accuracy.
- Focused D7.2 suite: 5/5 passed locally.

The reviewable D7.2 commit is `bd09658` on branch `codex/d7-2-graph-value-evaluation`.

## Completed D7.3 work on the current branch

- Added deterministic report generation from typed workflow facts.
- Required every numeric claim to cite known evidence available by the workflow cutoff.
- Reconciled report values and units exactly against the evidence catalogue and failed closed on mismatches.
- Collapsed duplicate source/synthesis facts into unique claim IDs.
- Added a byte-reproducible ZIP with JSON, Markdown, reconciliation CSV, and a hash manifest.
- Added the reconciled report table, artifact hash, and download to the Research workflow workspace.
- Focused D7.3 suite: 5/5 passed locally.

The reviewable D7.3 commit is `4be9b4c` on branch `codex/d7-3-reconciled-research-report`.

## Completed D7.4 work on the current branch

- Added an AST-based audit for missing accessible names, empty widget labels, deprecated width APIs, and unsafe HTML.
- Fixed the two unlabelled expandable evidence tables found by the audit.
- Added keyboard guidance and complete acceptance journeys for all five workspaces.
- Exposed the repeatable audit result in the Evidence graph & operations workspace.
- Focused D7.4 suite: 4/4 passed locally; the current app entry point and dashboard modules report zero findings.
- Live rendered browser acceptance passed across all five workspaces on 7 November 2026.
- The final operations view showed 6 nodes, 5 edges, graph/table exactness parity, 76% inspection reduction, 5 surfaces scanned, 0 static findings, and `verified_local_demo_not_hosted`.

The reviewable D7.4 commit is `acb084b` on branch `codex/d7-4-accessibility-walkthroughs`.

## Completed D7.5 work on the current branch

- Added read-only SQLite health manifests with integrity, schema, table counts, bytes, and SHA-256.
- Added source/attempt/failure/latest-attempt monitoring to the operations workspace.
- Added SQLite online backup through a unique partial file, integrity verification, schema/count comparison, and atomic completion.
- Added verified restore to a new path and a strict no-overwrite policy for both backup and recovery.
- Documented stop-the-app recovery drills and explicit owner-controlled retention, encryption, off-device, and multi-worker boundaries.
- Focused D7.5 suite: 5/5 passed locally, including a complete backup-and-restore drill and corrupt-database failure.

The reviewable D7.5 commit is `c71f69b` on branch `codex/d7-5-monitoring-recovery`.

## Completed D7.6 work on the current branch

- Added a reproducible release audit for Python support, required artifacts, high-signal tracked-secret patterns, and deployment-boundary language.
- Added a CLI that reports `ready_for_owner_review` or fails nonzero; it never merges, deploys, or approves a release.
- Added a reviewed deployment plan covering authentication, secrets, egress, backup, observability, concurrency, rollback, and owner gates.
- Added an owner-controlled release checklist whose CI, pull-request review, merge, and deployment gates remain deliberately unchecked.
- Focused D7.6 suite: 5/5 passed locally.
- Full deterministic non-UI D0–D7.6 suite: 127/127 passed locally.
- Static compilation passed for `app.py`, `src`, `scripts`, and `tests`; `git diff --check` passed.
- Local release check reported `ready_for_owner_review`, 4/4 checks passed, no missing artifacts, and no secret findings.

## D7 finish compatibility evidence

The exact stacked heads passed the four-job Windows/Ubuntu × Python 3.12/3.13 GitHub Actions matrix:

- D7.2 `bd096583c2211fb770025b8847a4d01ad5b59c4a`: run `42386407967` passed.
- D7.3 `4be9b4c3aec55b9b336ce196ea67a136889954e3`: run `42386413581` passed.
- D7.4 `fff9f93a8b6b7008b5ba392c88e77d9449adafcb`: run `42386811509` passed after making the new tests create their ignored runtime parent on a fresh checkout.
- D7.5 `bb77de965bf262fad6ac7f348ad8afca2f3a64d6`: run `42386811879` passed.
- D7.6 feature/test head `da26c2dcdb77a0898aa91e328921aba70f759e69`: run `42386810957` passed.

## Completed D8.1 work on the current branch

- Added registry search across complete ticker, company-name, sector, and alias tokens without fuzzy guesses.
- Added a browser-session watchlist for the bounded ALP/BET/GAM universe.
- Reused point-in-time return, volatility, restatement, and ratio functions in one comparable snapshot.
- Added indexed adjusted-price performance, market/fundamental comparison tables, source/availability evidence, and a stable SHA-256 snapshot identity.
- Added explicit empty-search, empty-selection, unknown-ticker, historical-cutoff, hand-calculation, normalization, and hash tests.
- Focused D8.1 suite: 8/8 passed locally.
- Deterministic non-UI D0–D8.1 suite: 135/135 passed locally using a repository-scoped temporary directory.
- Static compilation, accessibility audit, `git diff --check`, and the release-readiness check passed locally.
- D8.1 remains a local review branch until exact-head CI, owner review, and stack-order merge gates are recorded.

## Completed D8.2 work on the current branch

- Added bounded revenue, margin, current-assets, current-liabilities, debt, and equity shocks.
- Recalculated stressed revenue, net income, current ratio, and debt-to-equity from explicit formulas while retaining filing dimensions and the historical cutoff.
- Added Neutral, Downside, and Recovery starting assumptions plus fully adjustable native controls.
- Added base-versus-stressed charts, result tables, aggregate risk cards, and a deterministic scenario SHA-256.
- Kept the interface explicit that scenarios have no assigned probability and are not forecasts, valuations, or recommendations.
- Focused D8.2 suite: 7/7 passed locally.
- Deterministic non-UI D0–D8.2 suite: 142/142 passed locally using a repository-scoped temporary directory.
- Static compilation, accessibility audit, and `git diff --check` passed locally.
- D8.2 remains a local review branch until exact-head CI, owner review, and stack-order merge gates are recorded.

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
- Conservative entity and event linkage with frozen diagnostics and uncertainty states.
- A hash-verified filings corpus, lexical/dense retrieval comparison, and grounded extractive QA with abstention.
- Typed, budgeted research workflows with visible missing/conflict states.
- Release-aware event studies, yield curves, credit spreads, and quote-direction-aware FX analytics.
- A point-in-time non-causal evidence graph with a frozen graph-versus-table value comparison.
- A searchable, session-persistent analyst watchlist with indexed performance, comparable point-in-time fundamentals, and reproducible snapshot identity.
- Bounded deterministic company stress scenarios with explicit formulas, assumptions, and no probability claim.

## Known limitations and blockers

- SQLite currently targets one local application process; multi-worker hosting and automated retention are not implemented.
- D2 uses fictional offline fixtures; no live price, macro, or filing provider is integrated.
- The implemented filings QA and research workflows are bounded deterministic baselines, not general-purpose generative RAG or autonomous agents.
- Repository-authored diagnostic sets are too small for external model-validity claims.
- Official-provider availability is external and must remain visible when it fails.
- Live providers, scheduled processing, authentication, multi-worker hosting, and deployment remain owner/infrastructure decisions.
- D8.1 uses the same tiny fictional three-company fixture; it demonstrates workflow and calculation integrity, not market coverage or external validity.

## Next priorities

1. Obtain owner review of draft pull requests #15–#19 before any merge decision.
2. Validate D8.1–D8.2 in exact-head CI, then review their stacked pull requests before any merge decision.
3. Implement D8.3 research-run comparison as a separate stacked milestone.
4. Merge only in stack order if each diff remains approved and green.
5. Keep deployment unapproved until the separate operating-policy gates in `docs/DEPLOYMENT_PLAN.md` are satisfied.

## Remaining before a stable release

- Fresh-user installation and browser demonstration.
- Archive browser screenshots in the reviewed release artifact.
- Default CI matrix passing at each exact reviewed commit.
- Optional backend evidence clearly separated from default evidence.
- Owner review of the local-demo decision and deployment plan.
- Owner review and approval; no merge or deployment is authorised by this file.

Future sessions must verify current branch/HEAD and open PR state before relying on this snapshot. Record only work actually performed, including pass/fail/skip counts and exact commits.
