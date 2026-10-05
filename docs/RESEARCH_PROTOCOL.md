# Evidence and financial language research

Question: can finance-specific sentiment and source-linked brief construction
improve useful market information without adding unsupported claims?

## Implemented comparisons
1. Keyword sentiment versus frozen ProsusAI/finbert on independently labelled text.
2. Existing aggregate template versus an extractive, source-linked evidence brief.
3. Citation validity, exact extraction and human semantic-support judgments are
   separate measurements. A valid link is never counted as proof of entailment.

Use human sentiment labels and supported/unsupported/unclear claim judgments.
Report macro F1, accuracy, confusion matrices, coverage, abstention and runtime.
A pretrained model is not automatically tested on unseen data: check its training
corpora and keep a dated, independent evaluation set. The bundled author-labelled
synthetic cases exercise negation, neutral descriptions and unfamiliar wording;
they are diagnostics, not a financial-news performance benchmark.

## Provenance and timing
Sources are public Federal Reserve/ECB RSS feeds, or explicitly uploaded CSVs.
Each record carries URL, publisher label, publication, retrieval and availability
timestamps, article ID and data hashes. Live ingestion uses first observation as
availability. Uploaded archives can supply their own recorded available_at; that
field remains a user assertion requiring external verification. Publication alone
cannot establish availability in a historical trading study. Synthetic sources
never enter a sourced brief. Duplicate headlines count once; metadata records
failed/skipped feeds. Missing or irrelevant evidence triggers abstention.

The brief deliberately preserves headline wording. It establishes what a source
reported, not that the report is true, causal, comprehensive or tradeable. This
release does not use a generative LLM, make return forecasts or claim measured
hallucination reduction against such a model. The claim-audit API permits future
human-adjudicated comparisons without equating citations with factual support.

## Reproduce
`python scripts/run_research.py --live` downloads official feeds and records a
source snapshot, extractive brief, citation audit and settings. Add `--finbert`
after installing requirements-finbert.txt to run the frozen language model.
`--labels your_labels.csv` supplies a separate labelled evaluation set.
`python -m unittest discover -s tests -v` runs offline and UI checks.

FinBERT revision: f210365adea9d5d19ff6a99f8658d1d94f58f584.
The optional model downloads pretrained weights when explicitly selected; no
paid API is used. Failures are shown and do not silently substitute another model.

## Primary references
- Araci (2019), FinBERT: https://arxiv.org/abs/1908.10063
- Model and training description: https://huggingface.co/ProsusAI/finbert
- Federal Reserve feeds: https://www.federalreserve.gov/feeds/feeds.htm
- ECB feeds: https://www.ecb.europa.eu/home/html/rss.en.html
