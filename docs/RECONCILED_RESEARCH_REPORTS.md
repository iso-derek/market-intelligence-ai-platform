# Reconciled research reports

The research workflow can export a deterministic report bundle only after every numeric claim reconciles to eligible point-in-time evidence.

## Contract

Every report fact must have one or more evidence IDs. Each ID must exist in the supplied evidence catalogue, be available at or before the workflow cutoff, and match both the reported numeric value and unit. Unknown, future, mismatched, or uncited evidence fails closed.

Duplicate facts emitted by the source roles and synthesis role collapse into one claim. The JSON report records the workflow artifact hash, claim-level citations, reconciliation rows, limitations, and a canonical report SHA-256.

## Download bundle

The ZIP contains `report.json`, a readable `report.md`, `reconciliation.csv`, and `manifest.json`. The manifest hashes every payload file. ZIP timestamps are fixed so the same report produces byte-identical exports.

This is a deterministic reporting baseline. Numeric reconciliation and citation resolution do not prove that a claim is material, complete, causal, or suitable for an investment decision.
