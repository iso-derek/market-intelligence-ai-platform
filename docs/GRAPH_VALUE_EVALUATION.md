# Graph value evaluation

This milestone tests whether the evidence graph adds measured value over reading the same point-in-time edge table directly. It does not assume that a graph is better.

## Frozen comparison

`data/evaluation/graph_value_cases.csv` contains five authored lookup cases: two one-hop checks, two multi-hop provenance checks, and one historical negative case. Both methods receive the same eligible edges after the same availability cutoff.

- **Graph method:** builds an adjacency index once and traverses only outgoing edges.
- **Table method:** scans every eligible edge row at each traversal step.
- **Exactness:** the found/not-found state and complete relationship sequence must match the frozen expectation.
- **Inspection cost:** counts edges or rows examined by each deterministic implementation. It is an explanatory operation count, not a runtime benchmark.

Both methods are expected to be exact on this tiny fixture. The useful graph result is narrower: the adjacency representation avoids repeated row scans and exposes a bounded provenance path directly. That does not establish production-scale latency, analytical accuracy, or causal value.

## Guardrails

The comparison preserves historical availability, rejects paths beyond eight hops, never revisits a node in the same path, and retains the non-causal relationship allowlist. The case-file SHA-256 is exported with every report so results can be tied to the exact authored fixture.
