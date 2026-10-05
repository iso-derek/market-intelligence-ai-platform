"""Lightweight NLP sentiment and summary logic."""

from __future__ import annotations

import re
from collections import Counter

import pandas as pd


POSITIVE_WORDS = {
    "beats",
    "raises",
    "strong",
    "expansion",
    "record",
    "partnership",
    "growth",
    "upgrade",
    "resilient",
    "surge",
}
NEGATIVE_WORDS = {
    "misses",
    "probe",
    "weak",
    "pressure",
    "layoffs",
    "downgrade",
    "risk",
    "volatility",
    "loss",
    "concern",
}
RISK_TERMS = {"probe", "regulatory", "downgrade", "weak", "layoffs", "credit risk", "volatility", "margin pressure"}


def sentiment_score(text: str) -> float:
    tokens = re.findall(r"[a-z]+", str(text).lower())
    counts = Counter(tokens)
    positive = sum(counts[word] for word in POSITIVE_WORDS)
    negative = sum(counts[word] for word in NEGATIVE_WORDS)
    raw = positive - negative
    return max(-1.0, min(1.0, raw / 3))


def sentiment_label(score: float) -> str:
    if score > 0.15:
        return "Positive"
    if score < -0.15:
        return "Negative"
    return "Neutral"


def detect_risk_flags(text: str) -> str:
    lowered = str(text).lower()
    hits = [term for term in RISK_TERMS if term in lowered]
    return ", ".join(sorted(hits)) if hits else "None"


def score_news(df: pd.DataFrame) -> pd.DataFrame:
    output = df.copy()
    output["sentiment_score"] = output["headline"].apply(sentiment_score)
    output["sentiment_label"] = output["sentiment_score"].apply(sentiment_label)
    output["risk_flags"] = output["headline"].apply(detect_risk_flags)
    return output


def generate_market_summary(df: pd.DataFrame) -> str:
    """Generate an AI-style local summary without external APIs."""
    if df.empty:
        return "No headlines available for the selected filters."
    avg_sentiment = df["sentiment_score"].mean()
    top_companies = ", ".join(df["company"].value_counts().head(3).index)
    top_topics = ", ".join(df["topic"].value_counts().head(3).index)
    risk_count = int((df["risk_flags"] != "None").sum())
    tone = "positive" if avg_sentiment > 0.1 else "negative" if avg_sentiment < -0.1 else "mixed"
    return (
        f"Market tone is {tone}, with an average sentiment score of {avg_sentiment:.2f}. "
        f"The most mentioned companies are {top_companies}. Dominant themes include {top_topics}. "
        f"{risk_count} headlines contain explicit risk flags, so analysts should review the detailed news table."
    )
