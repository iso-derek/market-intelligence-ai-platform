"""Deterministic filing-passage retrieval and frozen relevance evaluation."""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import Normalizer


RETRIEVAL_METHODS = ("lexical", "dense_lsa")
REQUIRED_PASSAGE_COLUMNS = {
    "passage_id", "document_id", "company", "ticker", "page", "section", "text", "available_at"
}
REQUIRED_CASE_COLUMNS = {
    "case_id", "query", "relevant_passage_ids", "cutoff", "review_status", "split"
}


def _passage_text(passages: pd.DataFrame) -> list[str]:
    return (
        passages["company"].astype(str) + " " + passages["ticker"].astype(str) + " "
        + passages["section"].astype(str) + " " + passages["text"].astype(str)
    ).tolist()


def _validated_passages(passages: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_PASSAGE_COLUMNS.difference(passages.columns)
    if missing:
        raise ValueError(f"passages missing columns: {sorted(missing)}")
    if passages.empty:
        return passages.copy()
    if passages["passage_id"].duplicated().any():
        raise ValueError("passage_id must be unique")
    frame = passages.copy()
    frame["available_at"] = pd.to_datetime(frame["available_at"], utc=True, errors="raise")
    return frame


def rank_passages(
    passages: pd.DataFrame,
    query: str,
    method: str = "lexical",
    top_k: int = 5,
) -> pd.DataFrame:
    """Rank passages with a lexical TF-IDF or deterministic dense LSA baseline."""
    frame = _validated_passages(passages)
    query = str(query).strip()
    if not query:
        raise ValueError("query must not be empty")
    if method not in RETRIEVAL_METHODS:
        raise ValueError(f"unsupported retrieval method: {method}")
    if not isinstance(top_k, int) or top_k < 1:
        raise ValueError("top_k must be a positive integer")
    if frame.empty:
        return frame.assign(score=pd.Series(dtype=float), rank=pd.Series(dtype=int))

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
    document_matrix = vectorizer.fit_transform(_passage_text(frame))
    query_vector = vectorizer.transform([query])
    if method == "lexical":
        scores = cosine_similarity(document_matrix, query_vector).ravel()
    else:
        components = min(8, document_matrix.shape[0] - 1, document_matrix.shape[1] - 1)
        if components < 2:
            raise ValueError("dense_lsa requires at least three passages and three vocabulary terms")
        svd = TruncatedSVD(n_components=components, algorithm="randomized", random_state=0)
        normalizer = Normalizer(copy=False)
        dense_documents = normalizer.fit_transform(svd.fit_transform(document_matrix))
        dense_query = normalizer.transform(svd.transform(query_vector))
        scores = cosine_similarity(dense_documents, dense_query).ravel()

    order = sorted(range(len(frame)), key=lambda i: (-float(scores[i]), str(frame.iloc[i]["passage_id"])))[:top_k]
    ranked = frame.iloc[order].copy()
    ranked["score"] = [float(scores[index]) for index in order]
    ranked["rank"] = range(1, len(ranked) + 1)
    return ranked.reset_index(drop=True)


def rank_passages_as_of(
    passages: pd.DataFrame,
    query: str,
    cutoff: object,
    method: str = "lexical",
    top_k: int = 5,
) -> pd.DataFrame:
    """Filter by first availability before fitting or ranking either baseline."""
    frame = _validated_passages(passages)
    point = pd.Timestamp(cutoff)
    point = point.tz_localize("UTC") if point.tzinfo is None else point.tz_convert("UTC")
    eligible = frame.loc[frame["available_at"].le(point)].copy()
    return rank_passages(eligible, query, method=method, top_k=top_k)


def load_relevance_cases(path: str | Path) -> pd.DataFrame:
    """Load the frozen authored relevance judgements used by the baseline diagnostic."""
    path = Path(path)
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = REQUIRED_CASE_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"relevance cases missing columns: {sorted(missing)}")
    if frame.empty or frame["case_id"].duplicated().any():
        raise ValueError("relevance cases must be non-empty with unique case_id values")
    if frame[["case_id", "query", "relevant_passage_ids", "review_status", "split"]].eq("").any().any():
        raise ValueError("relevance cases contain empty required values")
    frame["cutoff"] = pd.to_datetime(frame["cutoff"], utc=True, errors="raise")
    frame["relevant_ids"] = frame["relevant_passage_ids"].map(
        lambda value: tuple(item.strip() for item in value.split("|") if item.strip())
    )
    if frame["relevant_ids"].map(len).eq(0).any():
        raise ValueError("every case must identify at least one relevant passage")
    return frame


def file_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _ndcg(ranked_ids: list[str], relevant_ids: set[str], top_k: int) -> float:
    dcg = sum(
        1.0 / np.log2(rank + 1)
        for rank, passage_id in enumerate(ranked_ids[:top_k], start=1)
        if passage_id in relevant_ids
    )
    ideal_hits = min(len(relevant_ids), top_k)
    ideal = sum(1.0 / np.log2(rank + 1) for rank in range(1, ideal_hits + 1))
    return float(dcg / ideal) if ideal else 0.0


def evaluate_retriever(
    passages: pd.DataFrame,
    cases: pd.DataFrame,
    method: str,
    top_k: int = 3,
) -> tuple[dict[str, object], pd.DataFrame]:
    """Evaluate one method with recall@k, reciprocal rank, and nDCG@k."""
    frame = _validated_passages(passages)
    if not REQUIRED_CASE_COLUMNS.issubset(cases.columns) or "relevant_ids" not in cases.columns:
        raise ValueError("cases must be loaded with load_relevance_cases")
    known_ids = set(frame["passage_id"])
    rows: list[dict[str, object]] = []
    for case in cases.to_dict("records"):
        relevant = set(case["relevant_ids"])
        unknown = relevant.difference(known_ids)
        if unknown:
            raise ValueError(f"{case['case_id']} references unknown passages: {sorted(unknown)}")
        eligible_relevant = set(
            frame.loc[
                frame["passage_id"].isin(relevant) & frame["available_at"].le(case["cutoff"]),
                "passage_id",
            ]
        )
        if eligible_relevant != relevant:
            raise ValueError(f"{case['case_id']} labels evidence unavailable at its cutoff")
        ranked = rank_passages_as_of(frame, case["query"], case["cutoff"], method, top_k)
        ranked_ids = ranked["passage_id"].tolist()
        relevant_ranks = [index for index, item in enumerate(ranked_ids, start=1) if item in relevant]
        rows.append(
            {
                "case_id": case["case_id"],
                "query": case["query"],
                "method": method,
                "cutoff": case["cutoff"],
                "relevant_passage_ids": "|".join(sorted(relevant)),
                "retrieved_passage_ids": "|".join(ranked_ids),
                f"recall_at_{top_k}": len(relevant.intersection(ranked_ids)) / len(relevant),
                "reciprocal_rank": 1.0 / min(relevant_ranks) if relevant_ranks else 0.0,
                f"ndcg_at_{top_k}": _ndcg(ranked_ids, relevant, top_k),
            }
        )
    details = pd.DataFrame(rows)
    summary = {
        "method": method,
        "top_k": top_k,
        "case_count": len(details),
        f"mean_recall_at_{top_k}": float(details[f"recall_at_{top_k}"].mean()),
        "mean_reciprocal_rank": float(details["reciprocal_rank"].mean()),
        f"mean_ndcg_at_{top_k}": float(details[f"ndcg_at_{top_k}"].mean()),
    }
    return summary, details
