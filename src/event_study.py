"""Release-aware, market-adjusted event-study mechanics."""
from __future__ import annotations

import pandas as pd

try:
    from .market_data import prices_as_of
except ImportError:
    from market_data import prices_as_of


def event_session(released_at: object, sessions: pd.Series, close_hour_utc: int = 21) -> pd.Timestamp:
    release = pd.Timestamp(released_at)
    release = release.tz_localize("UTC") if release.tzinfo is None else release.tz_convert("UTC")
    ordered = pd.Series(pd.to_datetime(sessions, utc=True)).sort_values().drop_duplicates()
    same_day = ordered.loc[ordered.dt.date == release.date()]
    if not same_day.empty and release.hour < close_hour_utc:
        return same_day.iloc[0]
    later = ordered.loc[ordered > release]
    if later.empty:
        raise ValueError("no trading session exists after the release")
    return later.iloc[0]


def market_adjusted_event_study(
    prices: pd.DataFrame,
    instrument: str,
    released_at: object,
    cutoff: object,
    pre: int = 1,
    post: int = 1,
) -> tuple[dict[str, object], pd.DataFrame]:
    if pre < 0 or post < 0:
        raise ValueError("event window bounds must be non-negative")
    eligible = prices_as_of(prices, cutoff)
    pivot = eligible.pivot(index="date", columns="instrument", values="adjusted_close").sort_index()
    if instrument not in pivot or len(pivot.columns) < 2:
        raise ValueError("event study requires the instrument and at least one peer")
    returns = pivot.pct_change(fill_method=None).dropna(how="all")
    session = event_session(released_at, pd.Series(pivot.index))
    if session not in returns.index:
        raise ValueError("event session has no prior close for return calculation")
    position = returns.index.get_loc(session)
    start, end = position - pre, position + post
    if start < 0 or end >= len(returns):
        raise ValueError("insufficient observations for the requested event window")
    window = returns.iloc[start:end + 1].copy()
    peers = [column for column in returns.columns if column != instrument]
    window["instrument_return"] = window[instrument]
    window["benchmark_return"] = window[peers].mean(axis=1)
    window["abnormal_return"] = window["instrument_return"] - window["benchmark_return"]
    window["relative_day"] = range(-pre, post + 1)
    window["cumulative_abnormal_return"] = window["abnormal_return"].cumsum()
    output = window.reset_index()[
        ["date", "relative_day", "instrument_return", "benchmark_return", "abnormal_return", "cumulative_abnormal_return"]
    ]
    summary = {
        "instrument": instrument, "released_at": pd.Timestamp(released_at), "event_session": session,
        "pre": pre, "post": post, "peer_count": len(peers),
        "car": float(output["abnormal_return"].sum()), "cutoff": pd.Timestamp(cutoff),
        "method": "equal_weight_peer_market_adjusted",
    }
    return summary, output
