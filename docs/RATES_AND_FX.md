# Fixed income and FX analytics

D6.2 adds deterministic educational fixtures for US Treasury yields, a fictional corporate yield, EUR/USD, and USD/NGN. Every record has an observation time, first-availability time, source, and explicit unit.

Credit spread in basis points is:

`spread_bps = (corporate yield percent - matched government yield percent) × 100`

FX uses `BASE/QUOTE`, with values and units expressed as `QUOTE per BASE`. The base-currency return is `latest quote / first quote - 1`. A positive EUR/USD return therefore means EUR strengthened versus USD; a positive USD/NGN return means USD strengthened versus NGN.

These fixtures contain two dates and do not support duration, convexity, carry, roll-down, hedging, statistical relationships, or investment advice.
