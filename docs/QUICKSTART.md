# Quick start and verified workflows

## Requirements

- Python 3.12 or 3.13
- Internet access only for first-time dependency installation, official-feed retrieval, or optional FinBERT weights
- No administrator privileges or environment activation required

## Start the dashboard

### Windows

Double-click `Start.cmd`, run `./Start.ps1`, or use:

```powershell
py -3.13 launch.py
```

The Windows scripts try Python 3.13, Python 3.12, and then a compatible `python` command. The launcher creates `.venv`, installs `requirements-tested.txt`, and opens Streamlit on `http://127.0.0.1:8503`.

### macOS or Linux

```bash
python3.12 launch.py
```

## Run checks

```bash
python launch.py tests
```

The default tests are offline. They mock optional model behavior and parse local RSS/Atom fixtures. Live provider availability and downloaded FinBERT weights require separate checks.

## Four core user journeys

### 1. Point-in-time market lab

1. In **Workspace**, choose **Market, macro & fundamentals**.
2. Keep the 1 March historical view and select ALP, BET, or GAM.
3. Compare raw and adjusted closes. ALP demonstrates why split-aware returns use adjusted close.
4. Open **Macro vintages**, then switch the historical view to 31 January. Confirm December CPI changes from the later revised value 3.0 to the initial value 2.9.
5. Open **Company peers**. Confirm ALP's complete report version changes between cutoffs and that units, filing time, availability time, and report version remain visible.
6. Read **Methodology** before interpreting the ratios or volatility.

All three companies and all values are fictional educational fixtures. This journey is offline and does not claim live market coverage.

### 2. Synthetic demonstration and abstention

1. Keep **Synthetic demonstration** selected.
2. Confirm the synthetic-data warning is visible.
3. Open **Evidence brief** and enter any query.
4. Confirm the app abstains because synthetic items are excluded from sourced evidence.
5. Inspect sentiment and risk flags in **News explorer** as demonstration outputs only.

### 3. Official evidence

1. Select **Official feeds**.
2. Review the enabled sources and latest status in the persistent registry.
3. Select one or more enabled sources and press **Fetch selected sources**.
4. Inspect each source's status, parsed count, skipped count, feed URL, and immutable snapshot hash.
5. Enter a query and UTC cutoff.
6. Open each linked source and download the research ZIP.
7. Inspect `articles.csv`, `brief.json`, `citation_audit.csv`, and `settings.json`.
8. Reopen the app to verify persisted evidence remains available without another fetch.

Open **Manage registered sources** to enable or disable a source, add a public HTTPS RSS/Atom URL, or export an exact stored snapshot. Each snapshot ZIP contains the original XML bytes, a manifest, and the exact normalised article records.

If every feed fails, the app stops with diagnostics. It does not replace official evidence with synthetic headlines.

The default database is `data/runtime/evidence.db`. Set `MARKET_INTELLIGENCE_DB` to use another location. Runtime databases are excluded from Git; back them up separately if the evidence history matters.

### 4. Dated CSV evidence

Upload a UTF-8 CSV containing:

```csv
headline,published_at,available_at,url,source
Policy rate held unchanged,2026-01-01T12:00:00Z,2026-01-01T12:05:00Z,https://example.org/policy,Example source
```

The system rejects empty headlines, invalid timestamps, availability before publication, unsafe URLs, invalid synthetic flags, and unusable schemas. A publication date alone does not prove historical system availability; supply a recorded `available_at` when you have one.

## Evaluate sentiment

Prepare distinct headlines with one of three exact labels:

```csv
headline,label
Company reports strong growth,Positive
Company warns of weak demand,Negative
Company publishes annual report,Neutral
```

Open **Research evaluation**, upload the file, and press **Evaluate selected sentiment model**. Record the dataset hash, model revision, label order, accuracy, macro F1, confusion matrix, and runtime together.

The included 18-item fixture is a functional diagnostic, not an external benchmark.

## Optional FinBERT

```bash
pip install -r requirements-finbert.txt
python scripts/run_research.py --finbert --labels data/evaluation/diagnostic_cases.csv
```

The model is pinned to revision `f210365adea9d5d19ff6a99f8658d1d94f58f584`. Its weights are not installed by the default launcher. Review the upstream terms recorded in `DATA_AND_MODEL_SOURCES.md` before use or deployment.

## Recorded research runs

```bash
python launch.py research
python launch.py research --live
```

Each run gets a unique `runs/<timestamp>-<id>/` folder with `execution.log`, `manifest.json`, `dependencies.txt`, and copies of changed supported output artifacts.

Failed runs are recorded. A zero exit code establishes execution only; inspect the data source, methodology, and limitations before using results.

## Troubleshooting

- **Dependency installation fails:** check network/proxy access to PyPI, then rerun. The launcher does not write its requirements marker until installation succeeds.
- **Official feeds fail:** inspect the diagnostics. Provider/network failure remains visible.
- **Registry rejects a URL:** registered sources must use public HTTPS endpoints; local, private, and reserved IP targets are rejected.
- **Database is locked:** run one local application process against each SQLite file, then retry.
- **FinBERT cannot run:** install the optional file and verify model-weight access. The app stops rather than using the keyword method silently.
- **Port 8503 is busy:** run `python launch.py --port 8513`.
- **Invalid CSV:** verify UTF-8 encoding, required columns, ISO timestamps, and public HTTP(S) URLs without embedded credentials.

## Hosting boundary

This milestone targets a verified local demo. A public host needs upload privacy controls, operating limits, source/model rights review, and secrets/persistence design. No hosted endpoint is claimed.
