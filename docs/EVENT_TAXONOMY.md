# Event taxonomy and linkage

D3.2 adds a transparent event baseline after entity resolution. It classifies headline language; it does not establish that an event happened, caused a price move, or is material to an investment decision.

## Taxonomy

The fixed `keyword-event-v1` rules cover Earnings, Guidance, Regulation, M&A, Financing, Operations, and Macroeconomic language. Each rule is a short, inspectable term list in `src/events.py`.

For each headline, the classifier counts matched terms by category:

- one highest-scoring category produces `classified`;
- a tie for the highest score produces `ambiguous` and preserves all tied candidates;
- no match produces `unknown`.

Matched terms, candidates, status, and rule version remain in every output row. The application never silently converts an ambiguous or unknown result into a named event.

## Entity and sector linkage

Event rows join to the D3.1 resolution audit by stable record ID. Every resolved company produces its own event link, so a multi-company headline can retain multiple company and sector links. Ambiguous entity aliases remain `ambiguous`; unknown entities remain `unlinked`.

The linkage says only that a registry entity and an event term appear in the same headline. It is not evidence of causality, exposure magnitude, or return impact.

## Labelled diagnostic

`data/evaluation/event_taxonomy_cases.csv` contains 24 repository-authored labelled headlines, including all seven categories plus unknown and ambiguous examples. Labels are stored separately from inference and the report exports:

- dataset SHA-256 and rule version;
- accuracy and macro F1;
- per-class precision, recall, F1, and support;
- confusion matrix and individual predictions;
- ambiguous and unknown prediction counts.

This small author-labelled fixture verifies mechanics and failure states. It is not an external benchmark and cannot establish real-world event-classification validity. A later evaluation should use a larger, independently sampled and double-reviewed corpus with an adjudication log.

## Limitations

- Rules are English-only exact phrases; they do not understand syntax or negation.
- One headline can describe several legitimate events; a tied score is deliberately unresolved.
- Headline linkage does not verify the underlying event or its timing.
- There is no materiality, novelty, severity, or price-impact model.
- Evaluation examples are intentionally compact and may share vocabulary with the rule definitions.
