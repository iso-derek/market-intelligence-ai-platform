"""Plotly chart helpers for market intelligence."""

from __future__ import annotations

import pandas as pd
import plotly.express as px


def sentiment_trend_chart(trends: pd.DataFrame):
    return px.line(trends, x="date", y="avg_sentiment", title="Market Sentiment Trend", markers=True)


def company_mentions_chart(mentions: pd.DataFrame):
    return px.bar(mentions.head(12), x="mentions", y="company", color="avg_sentiment", orientation="h", title="Most Mentioned Companies")


def sector_sentiment_chart(sectors: pd.DataFrame):
    return px.bar(sectors, x="sector", y="avg_sentiment", title="Average Sentiment by Sector")


def topic_chart(topics: pd.DataFrame):
    return px.treemap(topics, path=["topic"], values="mentions", color="avg_sentiment", title="Market Themes")
