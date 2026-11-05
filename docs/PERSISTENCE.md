# Evidence persistence and migrations

## Scope

D1 uses a local SQLite database to preserve registered sources, every fetch attempt, immutable raw-feed snapshots, article versions, and the first observed availability time for each stored version. The default file is `data/runtime/evidence.db`; set `MARKET_INTELLIGENCE_DB` to choose another path.

Runtime databases are excluded from Git. This prevents accidental publication of user-added sources or collected evidence, but it also means Git is not a backup. Copy the database and exported snapshot ZIPs to a controlled backup location when the history matters.

## Schema version 1

| Table | Purpose | Mutation model |
|---|---|---|
| `sources` | Registry, enabled state, last check, status, and error | Configuration and health fields update in place. |
| `source_attempts` | Every successful or failed retrieval attempt | Append only. |
| `snapshots` | Original feed bytes and SHA-256 identifiers | Immutable; duplicate source/payload imports are ignored. |
| `article_versions` | Normalised source-specific article versions | Immutable; a revised headline produces another version. |
| `snapshot_articles` | Snapshot membership and observed availability | Immutable; duplicate links are ignored. |

The database uses `PRAGMA user_version`. Application startup applies missing migrations transactionally. A database with a version newer than the application supports is rejected rather than guessed at or downgraded.

## Time semantics

- `published_at` is the publisher's timestamp.
- `retrieved_at` is when this system fetched the immutable payload.
- `available_at` is the first recorded time that article version was observed in a stored snapshot.

An article is eligible at cutoff `t` only when both `published_at <= t` and `available_at <= t`. Later imports do not rewrite earlier snapshots or expand an earlier cutoff result.

## Idempotency and revisions

The snapshot identifier is SHA-256 over the source ID and exact response bytes. Fetching identical bytes again records another attempt and updates source health, but it does not duplicate the snapshot or articles. If the provider revises a headline or timestamp, the normalised article identity changes and both versions remain reconstructable.

## Replay and export

`EvidenceStore.replay_snapshot(snapshot_hash)` reconstructs the normalised records tied to one immutable payload. `EvidenceStore.export_snapshot(snapshot_hash)` creates a ZIP containing:

- `snapshot.xml` — exact provider response bytes;
- `manifest.json` — source, retrieval, hash, and count metadata;
- `articles.csv` — exact normalised records from that snapshot.

## Failure behavior

Network, HTTP, XML, and validation failures create visible failed attempts and update the source's last status/error. They never create snapshot rows, never create synthetic replacements, and never erase previously stored evidence. HTTP GET retries are bounded to two retries for connection, read, HTTP 429, and selected 5xx failures.

## Current operating boundary

SQLite is appropriate for the verified local single-process workflow. Multi-worker concurrency, scheduled ingestion, retention rules, encrypted storage, automated backup/restore, and server deployment are not implemented. Those require a separate operating design and review.
