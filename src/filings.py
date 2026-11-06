"""Hash-verified bounded filings corpus with page and section provenance."""
from __future__ import annotations

import hashlib
from pathlib import Path
import re

import pandas as pd


MANIFEST_COLUMNS = {
    "document_id",
    "file_name",
    "company",
    "ticker",
    "form",
    "period_end",
    "filed_at",
    "available_at",
    "source_uri",
    "sha256",
}
MAX_DOCUMENT_BYTES = 2_000_000


def _safe_document_path(root: Path, file_name: str) -> Path:
    root = root.resolve()
    candidate = (root / file_name).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("filing path must remain inside the corpus root") from exc
    if not candidate.is_file():
        raise ValueError(f"filing document does not exist: {file_name}")
    return candidate


def load_filing_manifest(root: str | Path) -> pd.DataFrame:
    """Load and validate corpus-level metadata."""
    root = Path(root)
    manifest = pd.read_csv(root / "manifest.csv", dtype="string").fillna("")
    if missing := sorted(MANIFEST_COLUMNS.difference(manifest.columns)):
        raise ValueError(f"filing manifest is missing columns: {', '.join(missing)}")
    if manifest["document_id"].duplicated().any() or manifest["file_name"].duplicated().any():
        raise ValueError("filing document IDs and file names must be unique")
    for column in ["period_end", "filed_at", "available_at"]:
        manifest[column] = pd.to_datetime(manifest[column], utc=True, errors="coerce")
        if manifest[column].isna().any():
            raise ValueError(f"{column} must contain valid timestamps")
    if (manifest["filed_at"] < manifest["period_end"]).any():
        raise ValueError("filing time cannot precede period end")
    if (manifest["available_at"] < manifest["filed_at"]).any():
        raise ValueError("filing availability cannot precede filing time")
    if not manifest["sha256"].str.fullmatch(r"[0-9a-f]{64}").all():
        raise ValueError("filing hashes must be lowercase SHA-256 values")
    for file_name in manifest["file_name"]:
        _safe_document_path(root, file_name)
    return manifest.sort_values("document_id").reset_index(drop=True)


def _parse_sections(text: str, document: dict[str, object]) -> list[dict[str, object]]:
    page_parts = re.split(r"^=== PAGE (\d+) ===\s*$", text, flags=re.MULTILINE)
    if page_parts[0].strip() or len(page_parts) < 3:
        raise ValueError(f"{document['document_id']} must start with an explicit page marker")
    page_numbers = [int(page_parts[index]) for index in range(1, len(page_parts), 2)]
    if page_numbers != list(range(1, len(page_numbers) + 1)):
        raise ValueError(f"{document['document_id']} page numbers must be consecutive from 1")
    rows: list[dict[str, object]] = []
    for page_number, page_text in zip(page_numbers, page_parts[2::2]):
        section_parts = re.split(r"^## (.+?)\s*$", page_text, flags=re.MULTILINE)
        if section_parts[0].strip() or len(section_parts) < 3:
            raise ValueError(f"{document['document_id']} page {page_number} needs a section heading")
        for section_index, (section, content) in enumerate(zip(section_parts[1::2], section_parts[2::2]), start=1):
            content = re.sub(r"\s+", " ", content).strip()
            if not content:
                raise ValueError(f"{document['document_id']} contains an empty section")
            passage_id = f"{document['document_id']}:p{page_number}:s{section_index}"
            rows.append(
                {
                    **document,
                    "passage_id": passage_id,
                    "page": page_number,
                    "section": section.strip(),
                    "section_index": section_index,
                    "text": content,
                    "text_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                }
            )
    return rows


def load_filings_corpus(root: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Verify every document hash and return document and passage tables."""
    root = Path(root)
    manifest = load_filing_manifest(root)
    documents: list[dict[str, object]] = []
    passages: list[dict[str, object]] = []
    for row in manifest.to_dict("records"):
        path = _safe_document_path(root, str(row["file_name"]))
        payload = path.read_bytes()
        if len(payload) > MAX_DOCUMENT_BYTES:
            raise ValueError(f"{row['document_id']} exceeds the document size limit")
        actual_hash = hashlib.sha256(payload).hexdigest()
        if actual_hash != row["sha256"]:
            raise ValueError(f"hash mismatch for {row['document_id']}")
        if b"\x00" in payload:
            raise ValueError(f"{row['document_id']} contains null bytes")
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"{row['document_id']} must be UTF-8") from exc
        document = {**row, "bytes": len(payload), "hash_verified": True}
        parsed = _parse_sections(text, document)
        document["pages"] = max(item["page"] for item in parsed)
        document["sections"] = len(parsed)
        documents.append(document)
        passages.extend(parsed)
    return pd.DataFrame(documents), pd.DataFrame(passages)


def filings_as_of(
    documents: pd.DataFrame,
    passages: pd.DataFrame,
    cutoff: object,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return only documents available at the historical cutoff."""
    point = pd.Timestamp(cutoff)
    point = point.tz_localize("UTC") if point.tzinfo is None else point.tz_convert("UTC")
    eligible_documents = documents.loc[documents["available_at"].le(point)].copy()
    eligible_ids = set(eligible_documents["document_id"])
    eligible_passages = passages.loc[passages["document_id"].isin(eligible_ids)].copy()
    return eligible_documents.reset_index(drop=True), eligible_passages.reset_index(drop=True)
