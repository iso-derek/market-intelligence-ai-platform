"""SQLite persistence for source registry and point-in-time evidence snapshots."""

from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
import hashlib
import io
import ipaddress
import json
from pathlib import Path
import sqlite3
from urllib.parse import urlsplit
import zipfile

import pandas as pd


SCHEMA_VERSION = 1


def utc_iso(value=None) -> str:
    timestamp = pd.Timestamp.now(tz="UTC") if value is None else pd.to_datetime(value, utc=True)
    if pd.isna(timestamp):
        raise ValueError("A valid UTC timestamp is required.")
    return timestamp.isoformat()


def validate_feed_url(value: str) -> str:
    """Accept public HTTPS feed URLs and reject obvious local-network targets."""
    from ingestion import canonical_url

    url = canonical_url(value)
    parsed = urlsplit(url)
    if parsed.scheme != "https":
        raise ValueError("Registered feeds must use HTTPS.")
    hostname = (parsed.hostname or "").casefold().rstrip(".")
    if hostname == "localhost" or hostname.endswith((".localhost", ".local", ".internal")):
        raise ValueError("Registered feeds must not target a local hostname.")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return url
    if not address.is_global:
        raise ValueError("Registered feeds must not target a private or reserved IP address.")
    return url


@dataclass(frozen=True)
class SnapshotResult:
    snapshot_hash: str
    inserted: bool
    article_count: int


class EvidenceStore:
    """Versioned SQLite store with immutable snapshots and append-only attempts."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.migrate()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def migrate(self) -> None:
        with closing(self._connect()) as connection:
            version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            if version > SCHEMA_VERSION:
                raise RuntimeError(
                    f"Database schema {version} is newer than supported version {SCHEMA_VERSION}."
                )
            if version < 1:
                connection.executescript(
                    """
                    CREATE TABLE sources (
                        source_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL UNIQUE,
                        feed_url TEXT NOT NULL UNIQUE,
                        enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        last_checked_at TEXT,
                        last_status TEXT NOT NULL DEFAULT 'never'
                            CHECK (last_status IN ('never', 'ok', 'failed')),
                        last_error TEXT
                    );

                    CREATE TABLE snapshots (
                        snapshot_hash TEXT PRIMARY KEY,
                        payload_sha256 TEXT NOT NULL,
                        source_id TEXT NOT NULL REFERENCES sources(source_id),
                        retrieved_at TEXT NOT NULL,
                        payload BLOB NOT NULL,
                        article_count INTEGER NOT NULL CHECK (article_count >= 0),
                        UNIQUE (source_id, payload_sha256)
                    );

                    CREATE TABLE article_versions (
                        record_id TEXT PRIMARY KEY,
                        article_id TEXT NOT NULL UNIQUE,
                        source_id TEXT NOT NULL REFERENCES sources(source_id),
                        source_name TEXT NOT NULL,
                        canonical_url TEXT NOT NULL,
                        headline TEXT NOT NULL,
                        published_at TEXT NOT NULL,
                        synthetic INTEGER NOT NULL DEFAULT 0 CHECK (synthetic IN (0, 1))
                    );

                    CREATE TABLE snapshot_articles (
                        snapshot_hash TEXT NOT NULL REFERENCES snapshots(snapshot_hash),
                        record_id TEXT NOT NULL REFERENCES article_versions(record_id),
                        available_at TEXT NOT NULL,
                        PRIMARY KEY (snapshot_hash, record_id)
                    );

                    CREATE TABLE source_attempts (
                        attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source_id TEXT NOT NULL REFERENCES sources(source_id),
                        checked_at TEXT NOT NULL,
                        status TEXT NOT NULL CHECK (status IN ('ok', 'failed')),
                        snapshot_hash TEXT REFERENCES snapshots(snapshot_hash),
                        error TEXT
                    );

                    CREATE INDEX idx_snapshot_articles_available
                        ON snapshot_articles(available_at, record_id);
                    CREATE INDEX idx_article_versions_published
                        ON article_versions(published_at, article_id);
                    CREATE INDEX idx_source_attempts_source_time
                        ON source_attempts(source_id, checked_at DESC);

                    PRAGMA user_version = 1;
                    """
                )
                connection.commit()

    def schema_version(self) -> int:
        with closing(self._connect()) as connection:
            return int(connection.execute("PRAGMA user_version").fetchone()[0])

    def register_source(
        self,
        name: str,
        feed_url: str,
        *,
        source_id: str | None = None,
        enabled: bool = True,
        now=None,
    ) -> str:
        clean_name = " ".join(str(name).split())
        if not clean_name:
            raise ValueError("Source name cannot be empty.")
        clean_url = validate_feed_url(feed_url)
        identifier = source_id or hashlib.sha256(clean_url.encode()).hexdigest()[:16]
        if not identifier or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for character in identifier):
            raise ValueError("Source IDs may contain lowercase letters, digits, hyphens, and underscores.")
        timestamp = utc_iso(now)
        with closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT INTO sources(source_id, name, feed_url, enabled, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    name = excluded.name,
                    feed_url = excluded.feed_url,
                    enabled = excluded.enabled,
                    updated_at = excluded.updated_at
                """,
                (identifier, clean_name, clean_url, int(enabled), timestamp, timestamp),
            )
            connection.commit()
        return identifier

    def ensure_sources(self, sources: dict[str, str], *, now=None) -> None:
        for name, url in sources.items():
            source_id = hashlib.sha256(name.casefold().encode()).hexdigest()[:16]
            with closing(self._connect()) as connection:
                exists = connection.execute(
                    "SELECT 1 FROM sources WHERE source_id = ? OR name = ? OR feed_url = ?",
                    (source_id, name, validate_feed_url(url)),
                ).fetchone()
            if not exists:
                self.register_source(name, url, source_id=source_id, now=now)

    def list_sources(self, *, enabled_only: bool = False) -> pd.DataFrame:
        query = "SELECT * FROM sources"
        parameters: tuple[object, ...] = ()
        if enabled_only:
            query += " WHERE enabled = 1"
        query += " ORDER BY name"
        with closing(self._connect()) as connection:
            frame = pd.read_sql_query(query, connection, params=parameters)
        if not frame.empty:
            frame["enabled"] = frame["enabled"].astype(bool)
        return frame

    def set_enabled(self, source_id: str, enabled: bool, *, now=None) -> None:
        with closing(self._connect()) as connection:
            cursor = connection.execute(
                "UPDATE sources SET enabled = ?, updated_at = ? WHERE source_id = ?",
                (int(enabled), utc_iso(now), source_id),
            )
            if cursor.rowcount != 1:
                raise KeyError(f"Unknown source: {source_id}")
            connection.commit()

    def record_failure(self, source_id: str, error: str, *, checked_at=None) -> None:
        timestamp = utc_iso(checked_at)
        message = str(error).strip()[:2000] or "Unknown source failure"
        with closing(self._connect()) as connection:
            if not connection.execute(
                "SELECT 1 FROM sources WHERE source_id = ?", (source_id,)
            ).fetchone():
                raise KeyError(f"Unknown source: {source_id}")
            connection.execute(
                "INSERT INTO source_attempts(source_id, checked_at, status, error) VALUES (?, ?, 'failed', ?)",
                (source_id, timestamp, message),
            )
            connection.execute(
                """
                UPDATE sources
                SET last_checked_at = ?, last_status = 'failed', last_error = ?, updated_at = ?
                WHERE source_id = ?
                """,
                (timestamp, message, timestamp, source_id),
            )
            connection.commit()

    def record_snapshot(
        self,
        source_id: str,
        payload: bytes,
        articles: pd.DataFrame,
        *,
        retrieved_at=None,
    ) -> SnapshotResult:
        if not isinstance(payload, bytes) or not payload:
            raise ValueError("Snapshot payload must be non-empty bytes.")
        required = {"article_id", "headline", "url", "published_at", "available_at"}
        missing = required.difference(articles.columns)
        if missing:
            raise ValueError(f"Snapshot articles are missing columns: {', '.join(sorted(missing))}")
        timestamp = utc_iso(retrieved_at)
        payload_sha256 = hashlib.sha256(payload).hexdigest()
        snapshot_hash = hashlib.sha256(source_id.encode() + b"\0" + payload).hexdigest()
        with closing(self._connect()) as connection:
            source = connection.execute(
                "SELECT name FROM sources WHERE source_id = ?", (source_id,)
            ).fetchone()
            if source is None:
                raise KeyError(f"Unknown source: {source_id}")
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO snapshots(
                    snapshot_hash, payload_sha256, source_id, retrieved_at, payload, article_count
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (snapshot_hash, payload_sha256, source_id, timestamp, payload, len(articles)),
            )
            inserted = cursor.rowcount == 1
            for row in articles.itertuples(index=False):
                identity = f"{source_id}\n{row.article_id}"
                record_id = hashlib.sha256(identity.encode()).hexdigest()
                stored_article_id = record_id[:16]
                connection.execute(
                    """
                    INSERT OR IGNORE INTO article_versions(
                        record_id, article_id, source_id, source_name, canonical_url,
                        headline, published_at, synthetic
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record_id,
                        stored_article_id,
                        source_id,
                        source["name"],
                        str(row.url),
                        str(row.headline),
                        utc_iso(row.published_at),
                        int(bool(getattr(row, "synthetic", False))),
                    ),
                )
                connection.execute(
                    """
                    INSERT OR IGNORE INTO snapshot_articles(snapshot_hash, record_id, available_at)
                    VALUES (?, ?, ?)
                    """,
                    (snapshot_hash, record_id, utc_iso(row.available_at)),
                )
            connection.execute(
                """
                INSERT INTO source_attempts(source_id, checked_at, status, snapshot_hash)
                VALUES (?, ?, 'ok', ?)
                """,
                (source_id, timestamp, snapshot_hash),
            )
            connection.execute(
                """
                UPDATE sources
                SET last_checked_at = ?, last_status = 'ok', last_error = NULL, updated_at = ?
                WHERE source_id = ?
                """,
                (timestamp, timestamp, source_id),
            )
            connection.commit()
        return SnapshotResult(snapshot_hash, inserted, len(articles))

    def attempts(self, source_id: str | None = None) -> pd.DataFrame:
        query = "SELECT * FROM source_attempts"
        parameters: tuple[object, ...] = ()
        if source_id is not None:
            query += " WHERE source_id = ?"
            parameters = (source_id,)
        query += " ORDER BY checked_at, attempt_id"
        with closing(self._connect()) as connection:
            return pd.read_sql_query(query, connection, params=parameters)

    def snapshots(self) -> pd.DataFrame:
        with closing(self._connect()) as connection:
            return pd.read_sql_query(
                """
                SELECT snapshot_hash, payload_sha256, source_id, retrieved_at, article_count
                FROM snapshots ORDER BY retrieved_at, snapshot_hash
                """,
                connection,
            )

    def _evidence_query(self, where_clause: str, parameters: tuple[object, ...]) -> pd.DataFrame:
        with closing(self._connect()) as connection:
            frame = pd.read_sql_query(
                f"""
                SELECT
                    a.article_id,
                    a.headline,
                    a.canonical_url AS url,
                    a.published_at,
                    MIN(sa.available_at) AS available_at,
                    MIN(s.retrieved_at) AS retrieved_at,
                    a.source_name AS source,
                    a.synthetic
                FROM article_versions a
                JOIN snapshot_articles sa ON sa.record_id = a.record_id
                JOIN snapshots s ON s.snapshot_hash = sa.snapshot_hash
                {where_clause}
                GROUP BY a.record_id
                ORDER BY a.published_at, a.article_id
                """,
                connection,
                params=parameters,
            )
        return self._complete_frame(frame)

    @staticmethod
    def _complete_frame(frame: pd.DataFrame) -> pd.DataFrame:
        if frame.empty:
            return pd.DataFrame(
                columns=[
                    "article_id", "headline", "url", "published_at", "available_at",
                    "retrieved_at", "source", "synthetic", "company", "ticker",
                    "sector", "topic", "date", "month",
                ]
            )
        for column in ("published_at", "available_at", "retrieved_at"):
            frame[column] = pd.to_datetime(frame[column], utc=True)
        frame["synthetic"] = frame["synthetic"].astype(bool)
        frame["company"] = "Macro economy"
        frame["ticker"] = "MACRO"
        frame["sector"] = "Economy"
        frame["topic"] = "Policy"
        frame["date"] = frame["published_at"].dt.floor("D")
        frame["month"] = frame["published_at"].dt.strftime("%Y-%m")
        return frame

    def eligible_evidence(self, as_of=None) -> pd.DataFrame:
        cutoff = utc_iso(as_of)
        return self._evidence_query(
            "WHERE a.published_at <= ? AND sa.available_at <= ?",
            (cutoff, cutoff),
        )

    def replay_snapshot(self, snapshot_hash: str) -> pd.DataFrame:
        return self._evidence_query(
            "WHERE s.snapshot_hash = ?",
            (snapshot_hash,),
        )

    def export_snapshot(self, snapshot_hash: str) -> bytes:
        with closing(self._connect()) as connection:
            snapshot = connection.execute(
                """
                SELECT snapshot_hash, payload_sha256, source_id, retrieved_at, payload, article_count
                FROM snapshots WHERE snapshot_hash = ?
                """,
                (snapshot_hash,),
            ).fetchone()
        if snapshot is None:
            raise KeyError(f"Unknown snapshot: {snapshot_hash}")
        articles = self.replay_snapshot(snapshot_hash)
        manifest = {key: snapshot[key] for key in snapshot.keys() if key != "payload"}
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", json.dumps(manifest, indent=2))
            archive.writestr("articles.csv", articles.to_csv(index=False))
            archive.writestr("snapshot.xml", snapshot["payload"])
        return output.getvalue()
