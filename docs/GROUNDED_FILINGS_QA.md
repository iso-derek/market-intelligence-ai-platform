# Grounded filings question answering

D4.3 adds a deliberately bounded extractive answer layer over the D4.2 retriever. It returns exact source sentences with passage-level citations or a fixed abstention. It does not use a generative model and does not claim that a citation alone proves a broader interpretation.

## Answer contract

An answered result contains:

- exact text copied from one eligible passage;
- document, company, page, section, and first-availability metadata;
- the passage SHA-256;
- retrieval score, query coverage, and matched terms.

The service applies the historical cutoff before retrieval. It requires at least two supported non-entity content terms (or all terms for a one-term query). Missing facts and facts present only in later filings return the fixed abstention with no citation.

## Defensive boundary

Repository text is treated as untrusted evidence. Passages containing common instruction-like patterns such as requests to ignore prior instructions, reveal prompts, or follow embedded commands are excluded from answer support. This is a narrow regression guard, not a complete prompt-injection defence.

## Frozen diagnostic

The ten authored cases include six answerable numerical or disclosure questions and four unanswerable/cutoff questions. Evaluation separates:

- answer-versus-abstention status accuracy;
- expected passage citation accuracy;
- expected numerical/text token preservation;
- abstention recall on unanswerable cases.

These are fixture-author judgements over a tiny fictional corpus. They establish reproducible mechanics, not real-world QA quality, semantic entailment, or investment suitability.
