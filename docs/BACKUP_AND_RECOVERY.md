# Monitoring, backup, and recovery

The verified local target uses one SQLite database at `data/runtime/evidence.db` unless `MARKET_INTELLIGENCE_DB` specifies another location. Runtime data is excluded from Git; Git is not a backup.

## Health boundary

The operations view reports database initialization, SQLite integrity, schema version, source count, total and failed fetch attempts, latest attempt time, and file SHA-256. Provider failures remain evidence in the append-only attempt history.

## Create a backup

Use **Create verified local backup** in the operations view. The application uses SQLite's online backup API, writes to a unique `.partial` file, runs `PRAGMA integrity_check`, compares schema and table counts, and only then atomically renames the result. Existing destinations are never overwritten.

Backups remain under ignored `data/runtime/backups/` by default. Copy important backups to an access-controlled destination outside the repository using your normal backup process. Encryption and off-device retention are owner responsibilities.

## Restore drill

Do not restore over the active database. Stop the app, choose an unused destination, and call `restore_verified_backup(backup, destination)` from a trusted local Python session. The helper performs the same integrity/schema/count verification and refuses to overwrite an existing destination. Then set `MARKET_INTELLIGENCE_DB` to the restored path and run the full acceptance walkthrough before changing any production pointer.

## Retention and incident limits

No automated deletion policy is implemented. This avoids silent evidence loss but can grow disk use indefinitely. The owner must define retention, encryption, off-device copies, access control, and recovery objectives before hosting. Multi-worker writes, scheduled backup jobs, alert delivery, and disaster-recovery orchestration remain outside the verified local scope.
