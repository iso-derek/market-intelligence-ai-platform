# Analyst watchlist methodology

## Scope

D8.1 adds a cross-company analyst workspace for the fictional ALP, BET, and GAM fixture universe. It is an offline workflow demonstration, not live coverage, a recommendation, or a forecast.

The workspace supports:

- complete-token search across the registered ticker, canonical company name, sector, and aliases;
- a company selection that persists only within the current Streamlit browser session;
- adjusted-price performance indexed to 100 at each company's first eligible observation;
- point-in-time returns, annualized volatility, profitability, liquidity, and leverage;
- source and availability evidence for every selected company; and
- a deterministic SHA-256 identity for the sorted displayed snapshot.

## Time rule

Every eligible record must satisfy `available_at <= cutoff`. Price records must also have `date <= cutoff`. Fundamental data selects one complete report version, so later restatements cannot leak into an earlier view and facts from different report versions are never mixed.

## Calculations

The watchlist calls the existing tested market-data functions rather than maintaining a second set of formulas:

```text
cumulative return = latest adjusted close / first adjusted close - 1
annualized volatility = sample standard deviation(daily simple returns) × sqrt(252)
net margin = net income / revenue
current ratio = current assets / current liabilities
debt to equity = total debt / shareholders' equity
indexed close = adjusted close / first eligible adjusted close × 100
```

Revenue and net income retain their displayed filing currency and unit. Ratios and indexed prices are dimensionless.

## Search contract

Search normalizes case and punctuation, then requires every query token to occur as a complete token in at least one registered field. For example, `ALP`, `Alpha`, and `Industrials` match Alpha Industries; `LP` does not. This conservative rule avoids silently guessing fuzzy matches. A no-match query returns an explicit empty state.

Only registry companies with price coverage are included in the watchlist universe. The broader entity registry continues to support news-resolution tests but does not imply finance coverage.

## Snapshot identity

The snapshot is sorted by ticker and serialized with sorted field names, ISO timestamps, explicit nulls, and stable JSON separators before SHA-256 hashing. The hash is reproducible for identical rows and changes if a value, source, availability time, or cutoff changes. It identifies the displayed snapshot; it does not authenticate an external provider.

## Limitations

- The universe contains only three fictional companies and five fixture trading sessions.
- Session state is not durable across browser sessions and is not shared between users.
- Search is conservative token matching, not semantic entity search.
- Volatility from four daily returns is mechanically correct but statistically unstable.
- The workspace has no live provider, alerts, portfolio holdings, valuation model, or order execution.
