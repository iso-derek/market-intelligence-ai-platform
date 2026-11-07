"""SQLite health, verified backup, and non-destructive recovery helpers."""
from __future__ import annotations

from contextlib import closing
import hashlib
from pathlib import Path
import sqlite3


TABLES = ("sources", "source_attempts", "snapshots", "article_versions", "snapshot_articles")


def _connect_read_only(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise FileNotFoundError(path)
    connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def database_manifest(path: str | Path) -> dict[str, object]:
    path = Path(path)
    with closing(_connect_read_only(path)) as connection:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        schema_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
        counts = {table: int(connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]) for table in TABLES}
    return {
        "path": str(path.resolve()), "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "integrity": integrity, "schema_version": schema_version, "row_counts": counts,
    }


def operational_health(path: str | Path) -> dict[str, object]:
    path = Path(path)
    if not path.is_file():
        return {"status": "not_initialised", "database": str(path), "attempts": 0, "failed_attempts": 0, "sources": 0}
    manifest = database_manifest(path)
    with closing(_connect_read_only(path)) as connection:
        failed = int(connection.execute("SELECT COUNT(*) FROM source_attempts WHERE status = 'failed'").fetchone()[0])
        latest = connection.execute("SELECT MAX(checked_at) FROM source_attempts").fetchone()[0]
    return {
        "status": "healthy" if manifest["integrity"] == "ok" else "integrity_error",
        "database": str(path), "schema_version": manifest["schema_version"],
        "sources": manifest["row_counts"]["sources"],
        "attempts": manifest["row_counts"]["source_attempts"],
        "failed_attempts": failed, "latest_attempt_at": latest,
        "database_sha256": manifest["sha256"],
    }


def _sqlite_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(destination)
    partial = destination.with_name(destination.name + ".partial")
    if partial.exists():
        raise FileExistsError(partial)
    try:
        with closing(_connect_read_only(source)) as original, closing(sqlite3.connect(partial)) as copy:
            original.backup(copy)
        if database_manifest(partial)["integrity"] != "ok":
            raise RuntimeError("copied database failed integrity check")
        partial.replace(destination)
    except Exception:
        partial.unlink(missing_ok=True)
        raise


def create_verified_backup(source: str | Path, destination: str | Path) -> dict[str, object]:
    source, destination = Path(source), Path(destination)
    before = database_manifest(source)
    _sqlite_copy(source, destination)
    after = database_manifest(destination)
    if before["schema_version"] != after["schema_version"] or before["row_counts"] != after["row_counts"]:
        destination.unlink(missing_ok=True)
        raise RuntimeError("backup verification failed")
    return {"status": "verified", "source": before, "backup": after}


def restore_verified_backup(backup: str | Path, destination: str | Path) -> dict[str, object]:
    backup, destination = Path(backup), Path(destination)
    before = database_manifest(backup)
    _sqlite_copy(backup, destination)
    after = database_manifest(destination)
    if before["schema_version"] != after["schema_version"] or before["row_counts"] != after["row_counts"]:
        destination.unlink(missing_ok=True)
        raise RuntimeError("restore verification failed")
    return {"status": "verified", "backup": before, "restored": after}
