# Complete user walkthrough

This walkthrough exercises the verified local demonstration. Start the app with `python launch.py`, open the printed local URL, and use the labelled **Workspace** control in the sidebar. Keyboard users can move through controls with Tab and Shift+Tab, operate focused controls with Enter or Space, and change radio/select choices with arrow keys.

## 1. News evidence

1. Keep **Synthetic demonstration** selected and confirm the visible synthetic-data warning.
2. In **Evidence brief**, ask for `interest rates`; confirm the app abstains because generated examples cannot support a sourced brief.
3. Open **News explorer** and inspect provenance, sentiment, entity-resolution, and event-taxonomy tables. Confirm the captions state that sentiment and mentions do not predict returns.
4. Open **Research evaluation** and run the frozen sentiment and event diagnostics. Treat them as regression checks, not external validation.

Do not fetch official feeds during an offline acceptance run. A separate network-enabled run must keep failures visible and must never substitute synthetic evidence silently.

## 2. Market, macro & fundamentals

1. Select **Market, macro & fundamentals**.
2. Compare the 31 January and 1 March cutoffs. Confirm later records disappear at the earlier cutoff.
3. In **Market prices**, compare raw and adjusted ALP prices; the adjusted series removes the split discontinuity.
4. In **Macro vintages**, confirm the CPI vintage changes from 2.9 to 3.0 only after the later revision is available.
5. In **Company peers**, confirm ALP report version 2 is selected as a complete report rather than mixed with version 1.
6. Inspect **Event study** and **Rates & FX**; verify the timing, units, quote direction, and non-causal warnings.

## 3. Filings corpus

1. Select **Filings corpus** and use the later cutoff.
2. Confirm three reports, their SHA-256 identities, pages, sections, periods, and availability timestamps.
3. Compare lexical and dense-LSA retrieval. Both are deterministic authored-fixture baselines.
4. Ask the default warranty question and verify the exact answer sentence has page/section/hash citation evidence.
5. Ask a missing-dividend question and confirm the system abstains without inventing a citation.

## 4. Research workflow

1. Select **Research workflow**, choose ALP, and keep a five-second budget.
2. Confirm five role traces, the deliberately missing offline News role, explicit budgets, and no silent conflict.
3. Inspect the reconciled report table. Every numeric claim must match its cited value and unit.
4. Download the report bundle and inspect `report.json`, `report.md`, `reconciliation.csv`, and `manifest.json`.

## 5. Evidence graph & operations

1. Select **Evidence graph & operations** and compare the two cutoffs.
2. Confirm the earlier cutoff excludes the later filing chain.
3. Inspect bounded paths and verify relationship labels are provenance links, not causal claims.
4. Review the graph-versus-table evaluation: both methods are exact on the frozen cases; the graph only claims reduced repeated inspection and explicit paths.
5. Confirm the static accessibility audit passes and the operations status remains `verified_local_demo_not_hosted`.

## Acceptance boundaries

The walkthrough is complete only when the rendered app has no uncaught error, tables and charts have accessible names, visible controls have labels, evidence cutoffs change the eligible records, downloads are generated, and every limitation above remains visible. A successful walkthrough is not production deployment, investment validation, or approval to merge.
