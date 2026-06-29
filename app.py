"""Streamlit dashboard for AI-style financial market intelligence."""

from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from analytics import company_mentions, sector_sentiment, sentiment_trends, topic_summary  # noqa: E402
from data_generation import load_or_create_news  # noqa: E402
from modelling import generate_market_summary, score_news  # noqa: E402
from preprocessing import prepare_news  # noqa: E402
from visualisation import company_mentions_chart, sector_sentiment_chart, sentiment_trend_chart, topic_chart  # noqa: E402


st.set_page_config(page_title="Market Intelligence AI Platform", layout="wide")


@st.cache_data(show_spinner=False)
def get_data():
    return score_news(prepare_news(load_or_create_news()))


df = get_data()
st.title("Market Intelligence AI Platform")
st.caption("Local NLP market intelligence dashboard. Optional API integrations can be added through environment variables.")

with st.sidebar:
    st.header("Watchlist Filters")
    companies = st.multiselect("Companies", sorted(df["company"].unique()))
    sectors = st.multiselect("Sectors", sorted(df["sector"].unique()))
    topics = st.multiselect("Topics", sorted(df["topic"].unique()))
    labels = st.multiselect("Sentiment", ["Positive", "Neutral", "Negative"])

filtered = df.copy()
if companies:
    filtered = filtered[filtered["company"].isin(companies)]
if sectors:
    filtered = filtered[filtered["sector"].isin(sectors)]
if topics:
    filtered = filtered[filtered["topic"].isin(topics)]
if labels:
    filtered = filtered[filtered["sentiment_label"].isin(labels)]

cols = st.columns(4)
cols[0].metric("Headlines", f"{len(filtered):,}")
cols[1].metric("Avg Sentiment", f"{filtered['sentiment_score'].mean():.2f}" if len(filtered) else "N/A")
cols[2].metric("Companies", f"{filtered['company'].nunique():,}")
cols[3].metric("Risk Flags", f"{int((filtered['risk_flags'] != 'None').sum()):,}")

st.subheader("AI-Style Market Brief")
st.info(generate_market_summary(filtered))

tab1, tab2, tab3 = st.tabs(["Market Themes", "Company Watchlist", "News Explorer"])

with tab1:
    left, right = st.columns(2)
    left.plotly_chart(sentiment_trend_chart(sentiment_trends(filtered)), width="stretch")
    right.plotly_chart(sector_sentiment_chart(sector_sentiment(filtered)), width="stretch")
    st.plotly_chart(topic_chart(topic_summary(filtered)), width="stretch")

with tab2:
    mentions = company_mentions(filtered)
    st.plotly_chart(company_mentions_chart(mentions), width="stretch")
    st.dataframe(mentions.style.format({"avg_sentiment": "{:.2f}"}), width="stretch", hide_index=True)

with tab3:
    st.dataframe(
        filtered[["date", "company", "ticker", "sector", "topic", "headline", "sentiment_label", "sentiment_score", "risk_flags"]]
        .sort_values("date", ascending=False)
        .style.format({"sentiment_score": "{:.2f}"}),
        width="stretch",
        hide_index=True,
    )
