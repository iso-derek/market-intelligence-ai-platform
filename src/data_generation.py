"""Sample financial news data for market intelligence analytics."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
RAW_PATH = RAW_DIR / "sample_market_news.csv"

COMPANIES = {
    "Apple": ("AAPL", "Technology"),
    "Microsoft": ("MSFT", "Technology"),
    "Amazon": ("AMZN", "Consumer Discretionary"),
    "JPMorgan": ("JPM", "Financials"),
    "Goldman Sachs": ("GS", "Financials"),
    "BlackRock": ("BLK", "Asset Management"),
    "Tesla": ("TSLA", "Consumer Discretionary"),
    "Nvidia": ("NVDA", "Semiconductors"),
}

TOPICS = ["earnings", "regulation", "AI", "interest rates", "supply chain", "credit risk", "market volatility", "M&A"]
POSITIVE = ["beats expectations", "raises outlook", "strong demand", "margin expansion", "record revenue", "strategic partnership"]
NEGATIVE = ["misses estimates", "regulatory probe", "weak guidance", "margin pressure", "layoffs", "downgrade"]
NEUTRAL = ["announces update", "hosts investor day", "releases report", "reviews strategy", "comments on market conditions"]


def generate_news(n_rows: int = 600, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    start = date.today() - timedelta(days=180)
    company_names = list(COMPANIES.keys())
    for idx in range(n_rows):
        company = rng.choice(company_names)
        ticker, sector = COMPANIES[company]
        topic = rng.choice(TOPICS)
        tone_bucket = rng.choice(["positive", "negative", "neutral"], p=[0.42, 0.33, 0.25])
        phrase = rng.choice(POSITIVE if tone_bucket == "positive" else NEGATIVE if tone_bucket == "negative" else NEUTRAL)
        headline = f"{company} {phrase} as {topic} remains in focus"
        rows.append(
            {
                "date": start + timedelta(days=int(rng.integers(0, 181))),
                "company": company,
                "ticker": ticker,
                "sector": sector,
                "topic": topic,
                "headline": headline,
                "source": rng.choice(["Reuters sample", "MarketWatch sample", "Bloomberg-style sample", "Financial Times sample"]),
            }
        )
    return pd.DataFrame(rows).sort_values("date")


def save_news(path: Path = RAW_PATH) -> pd.DataFrame:
    path.parent.mkdir(parents=True, exist_ok=True)
    df = generate_news()
    df.to_csv(path, index=False)
    return df


def load_or_create_news(path: Path = RAW_PATH) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path, parse_dates=["date"])
    return save_news(path)


if __name__ == "__main__":
    data = save_news()
    print(f"Saved {len(data):,} sample headlines to {RAW_PATH}")
