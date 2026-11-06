# Frozen sentiment holdout and uncertainty

D3.3 separates functional diagnostics from a frozen sentiment holdout. The goal is reproducible evaluation evidence, not a claim that the keyword baseline or optional FinBERT is suitable for trading or production decisions.

## Corpus

`data/evaluation/sentiment_holdout.csv` contains 30 distinct repository-authored headlines: ten Positive, ten Negative, and ten Neutral. Each row has a case ID, source-group stratum, review status, and immutable `holdout` split marker.

The holdout is never used to fit the keyword lists. It is still small and author-reviewed rather than externally annotated, so it cannot establish broad generalization. The report hashes the exact supplied dataframe and records the backend/model revision.

## Metrics

The evaluation exports:

- accuracy and macro F1;
- ordered confusion matrix;
- precision, recall, F1, and support for every class;
- individual predictions;
- model/backend revision and data SHA-256;
- corpus split, source groups, and review status.

Macro F1 weights Negative, Neutral, and Positive equally. Per-class support remains visible so a class with few examples cannot be mistaken for strong evidence.

## Uncertainty

The default report uses 500 nonparametric bootstrap resamples of the labelled examples with seed 42. It reports percentile intervals at 95% confidence for accuracy and macro F1. These intervals measure sampling variation within this small authored corpus; they do not include labelling disagreement, source drift, or model-training uncertainty.

## Overlap review

For the transparent keyword baseline, the report lists every fixed rule term and the matched terms for each holdout case. It reports how many headlines contain at least one rule term. Some overlap is expected because the rules use ordinary finance language; the overlap must remain visible before anyone describes the results as unseen-data performance.

For optional FinBERT, absence of a local lexical match does not prove absence from pretraining or fine-tuning data. A genuine leakage audit would require access to upstream corpus lineage that is not available here.

## Responsible interpretation

- Sentiment classifies headline language; it does not verify facts or predict returns.
- The holdout is balanced by construction and is not representative of market-news prevalence.
- Bootstrap intervals on 30 items remain wide and conditional on these labels.
- Scores from the small 18-item historical diagnostic and this frozen holdout answer different questions and must not be pooled.
- External deployment requires a larger, independently sampled, double-reviewed corpus with adjudication and subgroup analysis.
