"""Transparent event taxonomy, entity linkage, and labelled evaluation."""
from __future__ import annotations

import hashlib
import re

import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support


EVENT_RULE_VERSION = "keyword-event-v1"
EVENT_RULES: dict[str, tuple[str, ...]] = {
    "Earnings": ("earnings", "revenue", "profit", "loss", "results", "beats estimates", "misses estimates"),
    "Guidance": ("guidance", "outlook", "forecast", "raises outlook", "cuts outlook"),
    "Regulation": ("regulation", "regulatory", "probe", "antitrust", "fine", "compliance"),
    "M&A": ("acquire", "acquisition", "merger", "takeover", "buyout"),
    "Financing": ("bond", "debt issuance", "share offering", "capital raise", "refinance", "credit facility"),
    "Operations": ("layoffs", "supply chain", "factory", "product launch", "partnership", "contract"),
    "Macroeconomic": ("interest rates", "inflation", "policy rate", "gdp", "unemployment", "central bank"),
}


def _matched_terms(text: str, terms: tuple[str, ...]) -> list[str]:
    """Return non-overlapping terms so nested phrases count only once."""
    candidates: list[tuple[int, int, str]] = []
    for term in terms:
        for match in re.finditer(rf"(?<![\w]){re.escape(term)}(?![\w])", text):
            candidates.append((match.start(), match.end(), term))
    candidates.sort(key=lambda item: (-(item[1] - item[0]), item[0], item[2]))
    accepted: list[tuple[int, int, str]] = []
    for candidate in candidates:
        start, end, _ = candidate
        if any(start >= prior_start and end <= prior_end for prior_start, prior_end, _ in accepted):
            continue
        accepted.append(candidate)
    return sorted(term for _, _, term in accepted)


def classify_event(text: object) -> dict[str, object]:
    """Classify one headline and preserve ties and no-match outcomes."""
    normalized = re.sub(r"\s+", " ", str(text).casefold()).strip()
    hits = {event_type: _matched_terms(normalized, terms) for event_type, terms in EVENT_RULES.items()}
    hits = {event_type: terms for event_type, terms in hits.items() if terms}
    if not hits:
        return {
            "event_type": "",
            "event_status": "unknown",
            "event_candidates": "",
            "matched_terms": "",
            "event_rule_version": EVENT_RULE_VERSION,
        }
    maximum = max(len(terms) for terms in hits.values())
    leaders = sorted(event_type for event_type, terms in hits.items() if len(terms) == maximum)
    matched = sorted({term for event_type in leaders for term in hits[event_type]})
    if len(leaders) > 1:
        return {
            "event_type": "",
            "event_status": "ambiguous",
            "event_candidates": "|".join(leaders),
            "matched_terms": "|".join(matched),
            "event_rule_version": EVENT_RULE_VERSION,
        }
    return {
        "event_type": leaders[0],
        "event_status": "classified",
        "event_candidates": leaders[0],
        "matched_terms": "|".join(matched),
        "event_rule_version": EVENT_RULE_VERSION,
    }


def classify_news_events(
    news: pd.DataFrame,
    text_column: str = "headline",
    id_column: str = "article_id",
) -> pd.DataFrame:
    """Classify every news row with a stable record identifier."""
    if text_column not in news:
        raise ValueError(f"news data is missing {text_column}")
    rows: list[dict[str, object]] = []
    for position, (_, row) in enumerate(news.iterrows()):
        record_id = str(row[id_column]) if id_column in news and pd.notna(row[id_column]) else str(position)
        rows.append(
            {
                "record_id": record_id,
                "headline": str(row[text_column]),
                **classify_event(row[text_column]),
            }
        )
    return pd.DataFrame(rows)


def link_events_to_entities(events: pd.DataFrame, resolutions: pd.DataFrame) -> pd.DataFrame:
    """Link event rows to resolved entities without forcing uncertain mentions."""
    required_events = {"record_id", "headline", "event_type", "event_status"}
    required_entities = {"record_id", "entity_id", "canonical_name", "ticker", "sector", "resolution_status", "candidate_ids"}
    if missing := sorted(required_events.difference(events.columns)):
        raise ValueError(f"events are missing columns: {', '.join(missing)}")
    if missing := sorted(required_entities.difference(resolutions.columns)):
        raise ValueError(f"resolutions are missing columns: {', '.join(missing)}")
    rows: list[dict[str, object]] = []
    for event in events.to_dict("records"):
        candidates = resolutions.loc[resolutions["record_id"].eq(event["record_id"])]
        resolved = candidates.loc[candidates["resolution_status"].eq("resolved")]
        if not resolved.empty:
            for entity in resolved.to_dict("records"):
                rows.append(
                    {
                        **event,
                        "entity_id": entity["entity_id"],
                        "canonical_name": entity["canonical_name"],
                        "ticker": entity["ticker"],
                        "sector": entity["sector"],
                        "entity_link_status": "linked",
                        "entity_candidates": entity["entity_id"],
                    }
                )
            continue
        ambiguous = candidates.loc[candidates["resolution_status"].eq("ambiguous")]
        rows.append(
            {
                **event,
                "entity_id": "",
                "canonical_name": "",
                "ticker": "",
                "sector": "",
                "entity_link_status": "ambiguous" if not ambiguous.empty else "unlinked",
                "entity_candidates": "|".join(sorted(set(ambiguous["candidate_ids"]))) if not ambiguous.empty else "",
            }
        )
    return pd.DataFrame(rows)


def event_outcome(classification: dict[str, object] | pd.Series) -> str:
    """Map a structured classification to one evaluation label."""
    status = str(classification["event_status"])
    if status == "classified":
        return str(classification["event_type"])
    return status.title()


def evaluate_event_classifier(cases: pd.DataFrame) -> dict[str, object]:
    """Evaluate the fixed rules against labels supplied separately from inference."""
    required = {"headline", "label"}
    if missing := sorted(required.difference(cases.columns)):
        raise ValueError(f"event evaluation is missing columns: {', '.join(missing)}")
    if cases.empty or cases["headline"].astype("string").str.strip().eq("").any():
        raise ValueError("event evaluation requires non-empty headlines")
    expected = cases["label"].astype("string").str.strip().tolist()
    predicted = [event_outcome(classify_event(headline)) for headline in cases["headline"]]
    labels = sorted(set(expected).union(predicted))
    precision, recall, f1, support = precision_recall_fscore_support(
        expected, predicted, labels=labels, zero_division=0
    )
    per_class = {
        label: {
            "precision": float(precision[index]),
            "recall": float(recall[index]),
            "f1": float(f1[index]),
            "support": int(support[index]),
        }
        for index, label in enumerate(labels)
    }
    digest = hashlib.sha256(cases[["headline", "label"]].to_csv(index=False).encode("utf-8")).hexdigest()
    return {
        "rule_version": EVENT_RULE_VERSION,
        "dataset_sha256": digest,
        "examples": len(cases),
        "labels": labels,
        "accuracy": float(accuracy_score(expected, predicted)),
        "macro_f1": float(sum(item["f1"] for item in per_class.values()) / len(per_class)),
        "per_class": per_class,
        "confusion_matrix": confusion_matrix(expected, predicted, labels=labels).tolist(),
        "predictions": predicted,
        "ambiguous_predictions": predicted.count("Ambiguous"),
        "unknown_predictions": predicted.count("Unknown"),
    }
