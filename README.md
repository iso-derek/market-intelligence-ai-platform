# Market Intelligence AI Platform

## Overview

Market Intelligence AI Platform is a Python NLP and analytics project for financial news monitoring, market sentiment scoring, company watchlists, topic analysis, and AI-style market summaries. It uses sample financial headlines by default and avoids paid APIs.

The project is suitable for MSc Finance & Data Science / Financial Engineering applications, fintech analytics roles, consulting analytics roles, market intelligence roles, and AI product portfolios.

## Business Problem

Analysts and finance teams monitor large volumes of market news across companies, sectors, and themes. Manual tracking is time-consuming and can miss emerging risk signals. This project demonstrates how lightweight NLP can turn headlines into sentiment trends, risk flags, company watchlists, and structured market briefs.

## Key Features

- Sample financial news dataset
- Company, sector, topic, and source fields
- Lightweight local sentiment scoring
- Positive, neutral, and negative sentiment labels
- Risk flag detection
- Company watchlist filters
- Market sentiment trend
- Most mentioned companies
- Sector sentiment analysis
- Market theme treemap
- AI-style local summary generation
- Source-linked extractive briefs and optional frozen FinBERT inference
- Streamlit dashboard

## Technologies Used

- Python
- pandas
- NumPy
- lightweight NLP
- Streamlit
- Plotly
- Optional FinBERT model

## Project Structure

```text
market-intelligence-ai-platform/
  README.md
  requirements.txt
  .gitignore
  app.py
  data/
    raw/
    processed/
  src/
    data_generation.py
    preprocessing.py
    modelling.py
    analytics.py
    visualisation.py
  notebooks/
  outputs/
  screenshots/
  assets/
```

## Methodology

1. Generate or load sample financial news headlines.
2. Clean headline text and prepare date, company, sector, and topic fields.
3. Score sentiment using a transparent local lexicon.
4. Detect risk-related terms.
5. Aggregate sentiment by date, sector, company, and topic.
6. Generate a local AI-style market brief from structured metrics.
7. Present insights in a Streamlit dashboard.

## How To Run

```bash
pip install -r requirements.txt
python src/data_generation.py
streamlit run app.py
```

## Dashboard Screenshots

Add screenshots to the `screenshots/` folder after running the app locally.

Suggested screenshots:

- Market brief
- Sentiment trend
- Company watchlist
- Sector sentiment
- News explorer

## Results / Insights

The dashboard helps answer:

- Which companies are most mentioned?
- Which sectors have positive or negative news flow?
- Which themes dominate market discussion?
- How many headlines contain risk flags?
- What is the overall market tone?

## Skills Demonstrated

- NLP feature engineering
- Sentiment analysis
- Market intelligence analytics
- Dashboard design
- Watchlist filtering
- Plotly visualisation
- API-safe project design

## Future Improvements

- Add live RSS ingestion
- Add optional OpenAI summaries
- Add named entity recognition
- Add topic modelling
- Add alerting workflow
- Add stock price reaction overlay
- Add scheduled news monitoring

## Author

Derek Ohimai Isokpehi  
GitHub: [iso-derek](https://github.com/iso-derek)

## Evidence and research upgrade

The dashboard now supports official RSS feeds, dated CSV imports, explicit data
provenance, duplicate removal, evidence retrieval with a historical cutoff,
source-linked extractive briefs, and independently labelled sentiment evaluation.
Synthetic headlines are clearly labelled and excluded from sourced briefs.
A missing feed or optional language model produces an error, not a hidden fallback.

```bash
pip install -r requirements.txt
streamlit run app.py
python -m unittest discover -s tests -v
python scripts/run_research.py --live
# Optional, downloads model weights; no paid API:
pip install -r requirements-finbert.txt
python scripts/run_research.py --finbert --labels data/evaluation/diagnostic_cases.csv
```

For CPU-only PyTorch, use the official CPU wheel index before installing the
optional file. Inputs, predictions and metadata export as reproducible bundles.
See [protocol](docs/RESEARCH_PROTOCOL.md) and [recorded checks](docs/RESEARCH_RESULTS.md).

The old keyword scorer remains a transparent comparison baseline. FinBERT is a
sentiment classifier; the brief is extractive, not a generative-LLM summary.
