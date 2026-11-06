# Filing retrieval baselines and evaluation

D4.2 adds two deterministic retrieval baselines over the hash-verified D4.1 passages. It does not add question answering or claim that retrieval proves an answer.

## Shared contract

Both methods accept the same passage table, query, historical cutoff, and `top_k`. The cutoff is applied before vocabulary fitting and ranking, so a later filing cannot influence an earlier result. Every result retains document, page, section, availability, and passage-hash provenance.

- `lexical`: unigram/bigram TF-IDF with cosine similarity.
- `dense_lsa`: the same TF-IDF matrix projected into eight or fewer latent semantic dimensions with seeded truncated SVD, L2 normalization, and cosine similarity.

The dense method is a transparent local vector baseline, not a pretrained language-model embedding. It can capture corpus-level co-occurrence but is not expected to understand finance or paraphrases reliably.

## Frozen diagnostic

`data/evaluation/filings_relevance_cases.csv` contains eight authored query-to-passage judgements. It is hashed and labelled `frozen_diagnostic`. Each judgement names the eligible passage expected at its cutoff.

Reported metrics are:

- recall@3: fraction of relevant passages retrieved in the first three results;
- mean reciprocal rank: inverse rank of the first relevant passage, averaged across queries;
- nDCG@3: relevance-weighted ranking quality in the first three results.

## Interpretation limits

The cases were written from this fictional corpus and reviewed by the fixture author, not by independent domain assessors. They are useful regression evidence but are too small and too close to the source text for model-selection or external-validity claims. A future corpus must add independent judgements, adversarial paraphrases, multi-relevant queries, and confidence intervals.

No metric verifies semantic support, numerical consistency, or answer faithfulness. D4.3 evaluates those properties separately and must preserve abstention when evidence is missing.
