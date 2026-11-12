# Research-run history

## Scope

D8.3 persists a typed workflow artifact and its reconciled report as one append-only local run. The feature reuses the repository's existing ignored `runs/` boundary while giving interactive workflow runs their own versioned, content-addressed schema.

This history answers four bounded questions:

1. Which workflow/report bytes were stored together?
2. Which company and historical cutoff produced them?
3. Have the stored bytes or manifest identity changed?
4. How do two verified runs differ on transparent workflow/report metrics?

It does not judge which run is better or whether any claim is financially significant.

## Write contract

Pressing **Save current research run** serializes `workflow.json` and `report.json`, hashes their exact bytes, builds a canonical identity payload, and writes all three files to a unique partial directory. Only after every file is complete is that directory renamed to:

```text
runs/workflow-<first 16 characters of run SHA-256>/
```

The full run SHA-256 covers the run kind, schema, research cutoff, company, question, status, artifact hashes, workflow identity, and report identity. The recording timestamp is metadata rather than content identity. Re-saving identical content returns the existing verified folder; it never overwrites it or creates a duplicate.

## Read and integrity contract

Before a typed run is listed or compared, the reader verifies:

- schema version and run kind;
- folder name against the canonical run identity;
- the exact required artifact set;
- safe relative artifact paths;
- SHA-256 of each stored artifact;
- workflow/report identities against the manifest; and
- full canonical run SHA-256.

Any mismatch fails closed and becomes a visible integrity error. Legacy CLI research-run folders can coexist under `runs/`; the typed-workflow history view ignores other run kinds rather than interpreting them as comparable artifacts.

## Historical-cutoff comparison

The workflow now supports the same 31 January and 1 March educational cutoffs used by the finance lab. The earlier run uses the eligible 2.9 CPI vintage and ALP net income of 100; the later run uses the revised 3.0 CPI vintage and ALP restated net income of 90.

Base/target comparison reports:

- whether the target cutoff is earlier, equal, or later;
- whether the company is the same;
- workflow status and steps used;
- missing roles and conflicts;
- facts and citations;
- reconciled claim count; and
- complete workflow/report identities.

The comparison describes stored outputs only. A later cutoff can legitimately include revised evidence, so a changed value is not automatically an error or improvement.

## Operating boundaries

- `runs/` is ignored by Git and remains on the local application filesystem.
- The implementation assumes one writer; it does not coordinate multiple workers or users.
- No retention, encryption, authentication, remote backup, or off-device replication is provided.
- A saved run is reproducibility evidence, not a release approval, forecast evaluation, or investment record.
- Production use requires the separate controls in `DEPLOYMENT_PLAN.md` and `BACKUP_AND_RECOVERY.md`.
