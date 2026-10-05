# Market evidence experiment — 2026-10-05

## Independently labelled diagnostic set

18 author-labelled synthetic headlines, balanced across Negative/Neutral/Positive, including negation and neutral descriptions. Labels are supplied separately from the classifiers. They are not externally adjudicated, and this small set is a diagnostic fixture, not a representative financial-news benchmark.

| Method | Accuracy | Macro F1 |
|---|---:|---:|
| Local lexicon v2 | .6667 | .6667 |
| ProsusAI FinBERT | .7222 | .7313 |

FinBERT was actually executed on CPU, using model revision `f210365adea9d5d19ff6a99f8658d1d94f58f584`. Its single additional correct prediction out of 18 is not evidence of a robust general advantage. No significance, unseen-corpus or novelty claim is made. Check training-data overlap before using an external benchmark.

Labelled input hash: `6a6754b213d5754ad76cd901d2e2601ebf508372617ec78979ddb25c0626e12e`.

## Official source ingestion

The live run retrieved 12 dated Federal Reserve monetary-policy entries and 14 ECB announcement entries, with zero skipped records. HTTP errors are reported and never replaced with synthetic articles.

- Fed feed hash: `6ef9f8ee2019c031b583ee3a64eec38170840e2ff4229ec92e43f49702857855`
- ECB feed hash: `c731b16d3d8fef3a39cc7b8fcda619428a9a4bddf19fec79be5182689a97694e`

Publication time and retrieval/availability time are preserved separately. An article fetched now cannot be treated as historically available merely because its publication date is old. Feed contents naturally change; downloaded study bundles preserve the actual article snapshot.

Briefs are source-linked headline extracts. Citation validity and exact headline matching are measured separately from optional human claim-support labels. This does not constitute a generative hallucination benchmark.

```bash
pip install -r requirements-finbert.txt
python scripts/run_research.py --live --finbert
```

Outputs include sentiment predictions/confusion matrices and the source-evidence bundle. Model loading and network conditions affect timing; the first observed CPU model load plus inference took about 54 seconds, not a controlled latency benchmark.
