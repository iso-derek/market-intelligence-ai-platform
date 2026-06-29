"""Market intelligence aggregation logic."""

from __future__ import annotations

import pandas as pd


def sentiment_trends(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("date", as_index=False).agg(avg_sentiment=("sentiment_score", "mean"), headlines=("headline", "count"))


def company_mentions(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["company", "ticker", "sector"], as_index=False)
        .agg(mentions=("headline", "count"), avg_sentiment=("sentiment_score", "mean"), risk_flags=("risk_flags", lambda s: int((s != "None").sum())))
        .sort_values("mentions", ascending=False)
    )


def sector_sentiment(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("sector", as_index=False)
        .agg(avg_sentiment=("sentiment_score", "mean"), mentions=("headline", "count"))
        .sort_values("avg_sentiment", ascending=False)
    )


def topic_summary(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("topic", as_index=False)
        .agg(mentions=("headline", "count"), avg_sentiment=("sentiment_score", "mean"))
        .sort_values("mentions", ascending=False)
    )
