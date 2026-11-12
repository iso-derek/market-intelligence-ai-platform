# Deterministic stress-scenario methodology

## Purpose and boundary

D8.2 adds transparent sensitivity analysis to the fictional watchlist universe. A scenario is a set of arithmetic assumptions, not a prediction. The application assigns no probability, estimates no statistical distribution, and does not produce a target price or investment recommendation.

## Inputs and bounds

| Assumption | Bound |
|---|---:|
| Revenue shock | -50% to +50% |
| Net-margin shock | -2,000 to +2,000 basis points |
| Current-assets shock | -50% to +50% |
| Current-liabilities shock | -50% to +50% |
| Debt shock | -50% to +100% |
| Equity shock | -50% to +50% |

The bounds prevent zero denominators and keep this educational interface within interpretable sensitivity ranges. A stressed net margin outside -100% to +100% is rejected.

Neutral, Downside, and Recovery are starting assumptions only. Every input remains visible and adjustable; the preset name does not assert likelihood.

## Formulas

For each company at the selected historical cutoff:

```text
stressed revenue = base revenue × (1 + revenue shock)
stressed net margin = base net margin + margin shock bps / 10,000
stressed net income = stressed revenue × stressed net margin

stressed current ratio = base current ratio
                         × (1 + current-assets shock)
                         / (1 + current-liabilities shock)

stressed debt to equity = base debt to equity
                          × (1 + debt shock)
                          / (1 + equity shock)
```

The ratio transformations are algebraically equivalent to shocking the underlying numerator and denominator by the displayed percentages. They do not model cash flows, covenants, taxes, interest expense, management response, or interactions between assumptions.

## Time and dimensions

Base values come from the watchlist snapshot and therefore retain the selected point-in-time cutoff, complete-report restatement rule, filing currency, and filing unit. The current fixture uses USD millions for all three companies, so aggregation is dimensionally valid only within this authored dataset.

## Scenario identity

The scenario SHA-256 covers the exact assumptions, sorted result records, cutoff, dimensions, and calculation-version label. It changes when an assumption or result changes. It is a reproducibility identifier, not an external signature.

## Interpretation limits

- Assumptions are independent; correlations and second-order effects are not estimated.
- The same shocks apply to every selected company.
- Balance-sheet ratios are static sensitivities, not a fully linked three-statement model.
- No probability, confidence interval, default likelihood, valuation, or return forecast is produced.
- Results inherit the tiny fictional fixture's lack of market coverage and external validity.
