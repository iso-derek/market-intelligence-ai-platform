"""Extractive, passage-cited question answering over the verified filings corpus."""
from __future__ import annotations

import re

import pandas as pd
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

try:
    from .retrieval import rank_passages_as_of
except ImportError:  # Streamlit adds src/ directly to sys.path.
    from retrieval import rank_passages_as_of


ABSTENTION = "The eligible filings do not contain enough evidence to answer this question."
INSTRUCTION_PATTERNS = (
    r"ignore (?:all |any )?(?:previous|prior) instructions?",
    r"system prompt",
    r"developer message",
    r"follow these instructions",
    r"reveal (?:the )?(?:prompt|secret|password|key)",
)
ENTITY_TERMS = {"alpha", "industries", "alp", "beta", "retail", "bet", "gamma", "software", "gam"}
ENTITY_ALIASES = {
    "ALP": ("alpha industries", "alpha", " alp "),
    "BET": ("beta retail", "beta", " bet "),
    "GAM": ("gamma software", "gamma", " gam "),
}
QUESTION_TERMS = {"what", "which", "who", "where", "when", "why", "how", "many", "much", "company", "filing", "report"}


def _tokens(value: str) -> list[str]:
    return [
        token for token in re.findall(r"[a-z0-9]+", str(value).lower())
        if token not in ENGLISH_STOP_WORDS and token not in ENTITY_TERMS and token not in QUESTION_TERMS
    ]


def _looks_like_instruction(text: str) -> bool:
    lowered = str(text).lower()
    return any(re.search(pattern, lowered) for pattern in INSTRUCTION_PATTERNS)


def _mentioned_tickers(question: str) -> set[str]:
    padded = f" {question.lower()} "
    return {
        ticker for ticker, aliases in ENTITY_ALIASES.items()
        if any(alias in padded for alias in aliases)
    }


def _best_extract(text: str, query_tokens: set[str], sentence_limit: int = 2) -> str:
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part.strip()]
    scored = []
    for index, sentence in enumerate(sentences):
        overlap = len(query_tokens.intersection(_tokens(sentence)))
        scored.append((overlap, index, sentence))
    selected = sorted(scored, key=lambda item: (-item[0], item[1]))[:sentence_limit]
    selected = sorted((item for item in selected if item[0] > 0), key=lambda item: item[1])
    return " ".join(item[2] for item in selected)


def answer_filing_question(
    passages: pd.DataFrame,
    question: str,
    cutoff: object,
    method: str = "lexical",
    retrieval_k: int = 5,
) -> dict[str, object]:
    """Return a verbatim extract with one auditable citation, or abstain."""
    question = str(question).strip()
    if not question:
        raise ValueError("question must not be empty")
    query_tokens = set(_tokens(question))
    if not query_tokens:
        return {
            "status": "abstained", "answer": ABSTENTION, "citations": [],
            "question": question, "method": method, "cutoff": pd.Timestamp(cutoff),
            "audit": {"reason": "no_content_terms", "eligible_candidates": 0},
        }
    mentioned_tickers = _mentioned_tickers(question)
    search_passages = passages
    if mentioned_tickers:
        search_passages = passages.loc[passages["ticker"].isin(mentioned_tickers)].copy()
    ranked = rank_passages_as_of(search_passages, question, cutoff, method=method, top_k=retrieval_k)
    candidates = []
    for row in ranked.to_dict("records"):
        if _looks_like_instruction(row["text"]):
            continue
        passage_tokens = set(_tokens(row["text"]))
        overlap = query_tokens.intersection(passage_tokens)
        coverage = len(overlap) / len(query_tokens)
        if len(overlap) >= min(2, len(query_tokens)) and float(row["score"]) > 0:
            candidates.append((coverage, float(row["score"]), row, overlap))
    if not candidates:
        return {
            "status": "abstained", "answer": ABSTENTION, "citations": [],
            "question": question, "method": method, "cutoff": pd.Timestamp(cutoff),
            "audit": {"reason": "insufficient_supported_overlap", "eligible_candidates": len(ranked)},
        }
    coverage, score, row, overlap = max(candidates, key=lambda item: (item[0], item[1], item[2]["passage_id"]))
    quote = _best_extract(str(row["text"]), query_tokens)
    if not quote:
        return {
            "status": "abstained", "answer": ABSTENTION, "citations": [],
            "question": question, "method": method, "cutoff": pd.Timestamp(cutoff),
            "audit": {"reason": "no_extractable_sentence", "eligible_candidates": len(ranked)},
        }
    citation = {
        "passage_id": row["passage_id"],
        "document_id": row["document_id"],
        "company": row["company"],
        "page": int(row["page"]),
        "section": row["section"],
        "available_at": row["available_at"],
        "text_sha256": row["text_sha256"],
        "quote": quote,
    }
    return {
        "status": "answered", "answer": quote, "citations": [citation],
        "question": question, "method": method, "cutoff": pd.Timestamp(cutoff),
        "audit": {
            "reason": "extractive_support", "retrieval_score": score, "query_coverage": coverage,
            "matched_terms": sorted(overlap), "eligible_candidates": len(ranked),
        },
    }


def load_qa_cases(path: str) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    required = {
        "case_id", "question", "cutoff", "expected_status", "expected_passage_id",
        "expected_tokens", "review_status", "split",
    }
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"QA cases missing columns: {sorted(missing)}")
    if frame.empty or frame["case_id"].duplicated().any():
        raise ValueError("QA cases must be non-empty with unique case IDs")
    if not set(frame["expected_status"]).issubset({"answered", "abstained"}):
        raise ValueError("expected_status must be answered or abstained")
    answered = frame["expected_status"].eq("answered")
    if frame.loc[answered, ["expected_passage_id", "expected_tokens"]].eq("").any().any():
        raise ValueError("answered cases require a passage and expected tokens")
    frame["cutoff"] = pd.to_datetime(frame["cutoff"], utc=True, errors="raise")
    return frame


def evaluate_filing_qa(passages: pd.DataFrame, cases: pd.DataFrame) -> tuple[dict[str, float | int], pd.DataFrame]:
    rows = []
    for case in cases.to_dict("records"):
        result = answer_filing_question(passages, case["question"], case["cutoff"])
        cited_ids = [item["passage_id"] for item in result["citations"]]
        expected_tokens = [item.strip().lower() for item in case["expected_tokens"].split("|") if item.strip()]
        answer_lower = str(result["answer"]).lower()
        token_support = all(token in answer_lower for token in expected_tokens)
        rows.append({
            "case_id": case["case_id"], "question": case["question"],
            "expected_status": case["expected_status"], "actual_status": result["status"],
            "status_correct": result["status"] == case["expected_status"],
            "expected_passage_id": case["expected_passage_id"],
            "cited_passage_ids": "|".join(cited_ids),
            "citation_correct": (
                case["expected_status"] == "abstained" and not cited_ids
            ) or case["expected_passage_id"] in cited_ids,
            "expected_tokens_supported": token_support if expected_tokens else result["status"] == "abstained",
            "answer": result["answer"],
        })
    details = pd.DataFrame(rows)
    answerable = details["expected_status"].eq("answered")
    unanswerable = ~answerable
    summary = {
        "case_count": len(details),
        "status_accuracy": float(details["status_correct"].mean()),
        "citation_accuracy": float(details["citation_correct"].mean()),
        "numerical_token_support": float(details.loc[answerable, "expected_tokens_supported"].mean()),
        "abstention_recall": float(details.loc[unanswerable, "actual_status"].eq("abstained").mean()),
    }
    return summary, details
