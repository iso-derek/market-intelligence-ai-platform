# Market, macro, and fundamental methodology

This document defines the bounded D2 analytical dataset, its time semantics, and the calculations shown in the dashboard. The bundled records are deterministic educational fixtures. They are not live observations, forecasts, or investment advice.

## Provider boundary

`MarketDataProvider` exposes three normalized tables: prices, macro observations, and fundamentals. `FixtureProvider` implements that protocol with local CSV files under `data/fixtures/` and performs no network access. A future provider must satisfy the same schemas and validation rules before its records reach calculations.

Provider acquisition, licensing, authentication, rate limits, and redistribution remain outside the calculation layer. Adding a provider does not make its values trustworthy by default; each adapter requires separate source-contract and acceptance testing.

## Bounded universe

- Instruments: ALP / Alpha Industries, BET / Beta Retail, and GAM / Gamma Software.
- Currencies: USD only in the fixture.
- Trading calendars: XNYS and XNAS, carried on every price observation.
- Macro series: consumer-price inflation and a policy rate.
- Fundamental period: fiscal year ending 31 December 2025.
- Units: price currency per share; macro units stated per series; accounting facts in USD millions; ratios dimensionless.

The names and values are fictional. They exist to make corporate actions, data revisions, and accounting restatements observable in a compact test dataset.

## Point-in-time rule

A record is eligible only when:

```text
available_at <= historical cutoff
```

Price records also require the market date to be no later than the cutoff. For macro history, the application retains every vintage and selects the latest eligible vintage for each series and observation period. For company accounts, it selects one complete eligible report version for each company and fiscal period. It never combines a fact from one report version with a fact from another.

`release_at` is the first announced macro release. `vintage_at` identifies an initial or revised vintage. `filed_at` is the asserted filing time. `available_at` is when the dataset can substantiate access. These timestamps answer different questions and must not be substituted for one another.

## Prices and corporate actions

Raw close is the observed unadjusted close. Adjusted close accounts for the fixture's corporate action and is the only series used for returns. ALP contains a two-for-one split example: the raw close moves from 104 to 53, while the adjusted series moves from 52 to 53. Keeping both fields makes the adjustment auditable.

For adjusted closes `P`:

```text
simple return_t = P_t / P_(t-1) - 1
cumulative return = P_last / P_first - 1
annualized volatility = sample_std(daily simple returns) × sqrt(252)
```

The 252-session convention is explicit and configurable in the calculation function. With only four returns per instrument, fixture volatility demonstrates mechanics; it is not a stable risk estimate.

## Fundamental ratios

The latest eligible fiscal period is used for each company:

```text
net margin = net income / revenue
current ratio = current assets / current liabilities
debt to equity = total debt / shareholders' equity
```

The implementation rejects zero denominators and missing required facts. Ratios are comparable only after the user confirms accounting policy, fiscal-period, currency, and unit consistency. The fixture does not attempt cross-GAAP normalization.

## Revision and restatement examples

- The December CPI observation is 2.9 in the initial vintage available on 15 January and 3.0 in the revised vintage available on 15 February.
- ALP initially reports net income of USD 100 million. Its complete second report version, available on 20 February, restates net income to USD 90 million.

The 31 January dashboard view must show the initial values. The 1 March view must show the revisions. Tests also delay part of a restatement and confirm that an incomplete new report version cannot be mixed with the old report.

## Validation and limitations

The test suite hand-checks split-aware returns, annualized volatility, cutoff exclusion, macro revisions, complete-report restatements, ratio values, units, calendars, and provider isolation. Validation proves the implementation against these fixtures, not the accuracy of an external data vendor.

There is no live price, macro, or filings adapter in D2. There are no total-return distributions, intraday data, exchange-holiday calculations, FX translation, fiscal-calendar normalization, consensus estimates, forecasts, or survivorship-bias controls. Those require explicit later scope and source review.
