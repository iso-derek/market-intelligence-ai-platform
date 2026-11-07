# Reviewed deployment plan — no deployment authorised

The current accepted target is a local, single-process Streamlit demonstration. This plan defines gates for a possible future hosted service; implementing it requires a separate owner decision.

## Candidate architecture

- One application process and one private persistent volume while SQLite remains the store.
- TLS termination and authentication in front of the application before any non-public uploads are accepted.
- Secrets supplied by the hosting platform, never committed files or client-side values.
- Network egress restricted to explicitly approved provider hosts.
- Encrypted off-device backups with a tested restore schedule and named owner.
- Structured health/error logs that exclude uploaded content, credentials, and full provider payloads.

## Mandatory gates

1. Exact candidate commit passes Windows and Ubuntu CI on Python 3.12 and 3.13.
2. Fresh environment installs `requirements-tested.txt`, `pip check` passes, and the local browser walkthrough passes.
3. Release check reports `ready_for_owner_review` with no tracked secrets.
4. Data/model terms, upload privacy, retention, deletion, backup, recovery, and incident ownership are approved.
5. Concurrency/load behavior is measured. SQLite must not be presented as a multi-worker service.
6. The owner reviews the complete stacked diff and explicitly approves merge and deployment separately.

## Rollback

Keep the last reviewed artifact and a verified pre-change database backup. A failed deployment is removed from traffic, the previous artifact is restored, and recovery targets a new database path before the pointer changes. Provider outages remain visible; do not replace missing live evidence with synthetic data.

## Current decision

No public hosting, DNS, cloud resource, account, credential, or deployment has been created. Passing local checks means only that the candidate is ready for owner review.
