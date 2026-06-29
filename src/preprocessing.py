"""Market news preprocessing."""

from __future__ import annotations

import re

import pandas as pd


def clean_text(text: str) -> str:
    text = str(text).strip()
    text = re.sub(r"\s+", " ", text)
    return text


def prepare_news(df: pd.DataFrame) -> pd.DataFrame:
    output = df.copy()
    output["date"] = pd.to_datetime(output["date"], errors="coerce")
    output["headline"] = output["headline"].apply(clean_text)
    output["company"] = output["company"].fillna("Unknown")
    output["sector"] = output["sector"].fillna("Unknown")
    output["topic"] = output["topic"].fillna("General")
    output["month"] = output["date"].dt.to_period("M").astype(str)
    return output.dropna(subset=["date", "headline"])
