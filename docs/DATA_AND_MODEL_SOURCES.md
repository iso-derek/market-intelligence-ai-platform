# Data and model sources

This document records the sources used by the current application and the constraints that must remain visible in research and deployment.

## D2 educational finance fixtures

- Files: `data/fixtures/prices.csv`, `macro_vintages.csv`, and `fundamentals.csv`.
- Use: deterministic validation of adjusted/raw prices, returns, volatility, macro vintages, accounting restatements, ratios, and point-in-time joins.
- Scope: three fictional USD companies, two fictionalized macro series, and one fiscal period.
- Access: local files only; the fixture provider performs no network requests.
- Rights: repository-authored educational test data. It must not be described as observed, vendor-sourced, or suitable for investment decisions.
- Time controls: every table carries availability; macro records also carry release/vintage time, and fundamentals carry filing time and report version.

The provider protocol is an engineering boundary, not evidence that a live provider is integrated. See `MARKET_DATA_METHODOLOGY.md` for schemas, formulas, and limitations.

## D3.1 entity registry

- File: `data/fixtures/entity_registry.csv`.
- Use: deterministic company, ticker, sector, and alias resolution for the bounded research interface.
- Origin: repository-authored educational metadata; it is not an exchange security master or licensed identifier feed.
- Resolution: exact, case-insensitive, word-boundary aliases with longest-span precedence.
- Uncertainty: shared aliases remain `ambiguous`; unmatched text remains `unknown`; neither state is silently coerced.
- Limitation: the registry does not handle corporate actions, historical ticker changes, subsidiaries, people, places, fuzzy spelling, or multilingual names.

## D3.2 event taxonomy diagnostic

- File: `data/evaluation/event_taxonomy_cases.csv`.
- Use: separately labelled functional evaluation of the fixed event taxonomy, including ambiguous and unknown outcomes.
- Origin: repository-authored educational diagnostics, not an external or representative market-news corpus.
- Exported identity: evaluation reports include the dataset SHA-256 and `keyword-event-v1` rule version.
- Limitation: 24 examples are insufficient for model-validity claims and share some vocabulary with the transparent rule list.

## D3.3 frozen sentiment holdout

- File: `data/evaluation/sentiment_holdout.csv`.
- Use: balanced frozen-split comparison for the keyword baseline and optional pinned FinBERT backend.
- Origin: 30 repository-authored, author-reviewed educational headlines; not an external benchmark.
- Identity: every report exports the exact dataframe SHA-256, backend, and model revision.
- Review: the lexicon report exports case-level overlap with its fixed positive/negative vocabulary.
- Limitation: balanced author labels, small sample size, and unknown upstream pretrained-corpus overlap constrain interpretation.

## D4.1 fictional filings corpus

- Files: `data/filings/*.txt` with `manifest.csv`.
- Use: page/section provenance, point-in-time availability, retrieval, citation, and numerical-consistency testing.
- Origin: repository-authored fictional annual reports; not issuer or regulator filings.
- Integrity: exact UTF-8 bytes are verified against manifest SHA-256 values; every normalized section receives a separate content hash.
- Limitation: no remote acquisition, arbitrary PDF parsing, OCR, tables, exhibits, or redistribution claim.

## Federal Reserve monetary-policy feed

- URL: `https://www.federalreserve.gov/feeds/press_monetary.xml`
- Use: dated titles and links for official monetary-policy announcements.
- Current behavior: fetched only after a user presses the button; response errors are returned in source diagnostics; feed bytes are hashed for the recorded run.
- Limitation: a feed entry is evidence of what the Federal Reserve published, not proof of a downstream market interpretation.
- Rights: review the Federal Reserve website's current terms before redistributing stored content beyond links and short metadata.

## European Central Bank announcements feed

- URL: `https://www.ecb.europa.eu/rss/press.html`
- Use: dated titles and links for official ECB announcements.
- Current behavior: same controls as the Federal Reserve feed.
- Limitation: coverage is limited to that feed and may change upstream.
- Rights: review the ECB website's current copyright and reuse terms before redistribution.

## Uploaded CSV data

- Required: `headline` plus `published_at` (or legacy `date`).
- Recommended: `available_at`, `retrieved_at`, `url`, `source`, company/ticker/sector/topic fields, and an explicit `synthetic` flag.
- The application validates timestamps and public HTTP(S) URLs, removes common tracking parameters, and rejects availability before publication.
- Users remain responsible for rights, privacy, confidentiality, and the truth of supplied availability timestamps.

## Synthetic demonstration

- Generated deterministically by `src/data_generation.py`.
- Used for interface mechanics and local sentiment examples.
- Always marked synthetic and excluded from source-grounded evidence retrieval.
- Must never be reported as observed market news or model-performance evidence.

## Keyword baseline

- Local fixed word lists in `src/modelling.py`.
- No downloaded model or external training corpus.
- Transparent comparator only; it is not presented as state-of-the-art NLP.

## Optional ProsusAI FinBERT

- Model ID: `ProsusAI/finbert`.
- Pinned revision: `f210365adea9d5d19ff6a99f8658d1d94f58f584`.
- Current code disables remote-code execution and expects positive, negative, and neutral probability outputs.
- Weights are not installed by default and may require a substantial first download.
- The upstream model card currently identifies the model-weights licence as CC BY-NC-SA 4.0. Verify the model card and applicability to the intended use at the time of deployment; do not assume commercial permission.
- Model outputs are sentiment classifications, not factual verification, event causality, or forecasts of returns.

## Provenance fields

The current ingestion contract distinguishes:

- `published_at`: time asserted by the source.
- `retrieved_at`: time this ingestion run fetched or received the item.
- `available_at`: earliest time the application can substantiate that the item was available to it.
- `article_id`: stable hash of canonical URL, headline, and publication time.
- `feed_sha256` / dataset hash: content identity for reproducibility.

Historical research must filter on both publication and availability. Backdating `available_at` from an old publication date creates look-ahead bias.

## Review cadence

Recheck URLs, schemas, access rules, model terms, and redistribution constraints before every public deployment or material source expansion. Record changes in `DEVELOPMENT_STATUS.md` and the relevant research bundle.
