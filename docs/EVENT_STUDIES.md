# Release-aware event studies

D6.1 adds a deterministic market-adjusted event-study diagnostic. A release before the 21:00 UTC fixture close maps to that trading session; an after-close or non-trading-day release maps to the next available session. Price records must also be available by the analysis cutoff.

For instrument return `r_i,t` and the equal-weight return of the other fixture instruments `r_m,t`:

`AR_i,t = r_i,t - r_m,t`

`CAR_i,[a,b] = sum(AR_i,t)` for relative days `a` through `b`.

The dashboard uses a three-session `[-1,+1]` window. The fixture is too short for a market-model estimation window, standard errors, multiple-event inference, or causal claims. Results are educational mechanics, not evidence that the release caused the return.
