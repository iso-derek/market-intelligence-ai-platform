"""Deterministic entity and ticker resolution with explicit uncertainty states."""
from __future__ import annotations

from pathlib import Path
import re

import pandas as pd


REGISTRY_COLUMNS = {
    "entity_id",
    "canonical_name",
    "ticker",
    "sector",
    "aliases",
    "active_from",
    "active_to",
}
RESOLUTION_VERSION = "exact-alias-v1"


def load_entity_registry(path: str | Path) -> pd.DataFrame:
    """Load and validate the versioned entity registry fixture."""
    registry = pd.read_csv(path, dtype="string").fillna("")
    missing = sorted(REGISTRY_COLUMNS.difference(registry.columns))
    if missing:
        raise ValueError(f"entity registry is missing columns: {', '.join(missing)}")
    if registry["entity_id"].duplicated().any():
        raise ValueError("entity_id values must be unique")
    if registry[["entity_id", "canonical_name", "ticker", "sector"]].apply(
        lambda column: column.str.strip().eq("").any()
    ).any():
        raise ValueError("entity identifiers, names, tickers, and sectors cannot be blank")
    registry["active_from"] = pd.to_datetime(registry["active_from"], utc=True, errors="coerce")
    registry["active_to"] = pd.to_datetime(registry["active_to"], utc=True, errors="coerce")
    if registry["active_from"].isna().any():
        raise ValueError("active_from must contain valid timestamps")
    if (registry["active_to"].notna() & registry["active_to"].lt(registry["active_from"])).any():
        raise ValueError("active_to cannot precede active_from")
    return registry.sort_values("entity_id").reset_index(drop=True)


def _alias_index(registry: pd.DataFrame) -> dict[str, list[dict[str, str]]]:
    aliases: dict[str, list[dict[str, str]]] = {}
    for row in registry.itertuples(index=False):
        values = {row.canonical_name, row.ticker}
        values.update(alias.strip() for alias in row.aliases.split("|") if alias.strip())
        entity = {
            "entity_id": row.entity_id,
            "canonical_name": row.canonical_name,
            "ticker": row.ticker,
            "sector": row.sector,
        }
        for value in values:
            key = re.sub(r"\s+", " ", value.casefold()).strip()
            if key:
                bucket = aliases.setdefault(key, [])
                if not any(existing["entity_id"] == entity["entity_id"] for existing in bucket):
                    bucket.append(entity)
    return aliases


def _matches(text: str, aliases: dict[str, list[dict[str, str]]]) -> list[tuple[int, int, str]]:
    candidates: list[tuple[int, int, str]] = []
    for alias in aliases:
        pattern = rf"(?<![\w])\$?{re.escape(alias)}(?![\w])"
        for match in re.finditer(pattern, text.casefold()):
            candidates.append((match.start(), match.end(), alias))
    candidates.sort(key=lambda item: (-(item[1] - item[0]), item[0], item[2]))
    accepted: list[tuple[int, int, str]] = []
    for candidate in candidates:
        start, end, _ = candidate
        if any(start >= existing_start and end <= existing_end for existing_start, existing_end, _ in accepted):
            continue
        accepted.append(candidate)
    return sorted(accepted, key=lambda item: item[0])


def resolve_text(text: object, registry: pd.DataFrame) -> list[dict[str, str]]:
    """Resolve all entity mentions in text without guessing.

    A shared alias produces one ``ambiguous`` record containing every candidate.
    Text without a registry match produces one ``unknown`` record.
    """
    value = re.sub(r"\s+", " ", str(text)).strip()
    aliases = _alias_index(registry)
    matches = _matches(value, aliases)
    if not matches:
        return [
            {
                "mention": "",
                "matched_alias": "",
                "entity_id": "",
                "canonical_name": "",
                "ticker": "",
                "sector": "",
                "resolution_status": "unknown",
                "candidate_ids": "",
                "resolution_version": RESOLUTION_VERSION,
            }
        ]

    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for start, end, alias in matches:
        entities = sorted(aliases[alias], key=lambda item: item["entity_id"])
        mention = value[start:end].lstrip("$")
        if len(entities) > 1:
            candidate_ids = "|".join(entity["entity_id"] for entity in entities)
            key = ("ambiguous", candidate_ids)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "mention": mention,
                    "matched_alias": alias,
                    "entity_id": "",
                    "canonical_name": "",
                    "ticker": "",
                    "sector": "",
                    "resolution_status": "ambiguous",
                    "candidate_ids": candidate_ids,
                    "resolution_version": RESOLUTION_VERSION,
                }
            )
            continue
        entity = entities[0]
        key = ("resolved", entity["entity_id"])
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "mention": mention,
                "matched_alias": alias,
                **entity,
                "resolution_status": "resolved",
                "candidate_ids": entity["entity_id"],
                "resolution_version": RESOLUTION_VERSION,
            }
        )
    return rows


def resolve_news_entities(
    news: pd.DataFrame,
    registry: pd.DataFrame,
    text_column: str = "headline",
    id_column: str = "article_id",
) -> pd.DataFrame:
    """Return one or more auditable resolution rows for every news record."""
    if text_column not in news:
        raise ValueError(f"news data is missing {text_column}")
    output: list[dict[str, object]] = []
    for position, (_, row) in enumerate(news.iterrows()):
        record_id = str(row[id_column]) if id_column in news and pd.notna(row[id_column]) else str(position)
        for resolution in resolve_text(row[text_column], registry):
            output.append(
                {
                    "record_id": record_id,
                    "headline": str(row[text_column]),
                    **resolution,
                }
            )
    return pd.DataFrame(output)


def resolution_summary(resolutions: pd.DataFrame) -> dict[str, int]:
    """Count unique input records by their most conservative status."""
    counts = {"resolved": 0, "ambiguous": 0, "unknown": 0}
    if resolutions.empty:
        return counts
    for _, group in resolutions.groupby("record_id"):
        statuses = set(group["resolution_status"])
        status = "ambiguous" if "ambiguous" in statuses else "resolved" if "resolved" in statuses else "unknown"
        counts[status] += 1
    return counts
