"""Streamlit presentation for the verified local filings corpus."""
from pathlib import Path

import pandas as pd
import streamlit as st

from filings import filings_as_of, load_filings_corpus
from filings_qa import answer_filing_question, evaluate_filing_qa, load_qa_cases
from retrieval import evaluate_retriever, file_sha256, load_relevance_cases, rank_passages


CORPUS_ROOT = Path(__file__).resolve().parents[1] / "data" / "filings"
RELEVANCE_CASES = Path(__file__).resolve().parents[1] / "data" / "evaluation" / "filings_relevance_cases.csv"
QA_CASES = Path(__file__).resolve().parents[1] / "data" / "evaluation" / "filings_qa_cases.csv"
CUTOFFS = {
    "23 January 2026 — Beta only": "2026-01-23T23:59:59Z",
    "1 February 2026 — Beta and Gamma": "2026-02-01T23:59:59Z",
    "1 March 2026 — all reports": "2026-03-01T23:59:59Z",
}


@st.cache_data
def load_verified_filings(root: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    return load_filings_corpus(root)


@st.cache_data
def load_frozen_relevance_cases(path: str) -> pd.DataFrame:
    return load_relevance_cases(path)


@st.cache_data
def load_frozen_qa_cases(path: str) -> pd.DataFrame:
    return load_qa_cases(path)


def render_filings_dashboard() -> None:
    documents, passages = load_verified_filings(str(CORPUS_ROOT))
    with st.sidebar:
        st.header("Filings controls")
        cutoff_label = st.selectbox("Corpus cutoff", list(CUTOFFS), index=2, key="filings_cutoff")
        st.info("The corpus contains fictional repository-authored reports for retrieval and citation testing.")
    eligible_documents, eligible_passages = filings_as_of(documents, passages, CUTOFFS[cutoff_label])

    st.subheader("Verified filings corpus")
    st.caption(f"Point-in-time cutoff: {pd.Timestamp(CUTOFFS[cutoff_label]).isoformat()}")
    cards = st.columns(4)
    cards[0].metric("Eligible reports", len(eligible_documents), border=True)
    cards[1].metric("Verified hashes", int(eligible_documents.hash_verified.sum()), border=True)
    cards[2].metric("Pages", int(eligible_documents.pages.sum()), border=True)
    cards[3].metric("Sections", len(eligible_passages), border=True)

    display_documents = eligible_documents[
        ["document_id", "company", "ticker", "form", "period_end", "filed_at", "available_at", "pages", "sections", "sha256", "source_uri"]
    ].rename(
        columns={
            "document_id": "Document ID", "company": "Company", "ticker": "Ticker", "form": "Form",
            "period_end": "Period end", "filed_at": "Filed at", "available_at": "Available at",
            "pages": "Pages", "sections": "Sections", "sha256": "Document SHA-256", "source_uri": "Source URI",
        }
    )
    st.dataframe(display_documents, hide_index=True, alt="Hash-verified filing documents eligible at the selected cutoff")
    if eligible_documents.empty:
        st.info("No filing was available at this cutoff.")
        return

    selected_id = st.selectbox(
        "Inspect report",
        eligible_documents["document_id"].tolist(),
        format_func=lambda value: eligible_documents.set_index("document_id").loc[value, "company"],
        key="filing_document",
    )
    selected = eligible_passages.loc[eligible_passages.document_id.eq(selected_id)]
    st.subheader("Page and section evidence")
    st.dataframe(
        selected[["page", "section", "period_end", "available_at", "text", "text_sha256"]].rename(
            columns={
                "page": "Page", "section": "Section", "period_end": "Period end",
                "available_at": "Available at", "text": "Text", "text_sha256": "Passage SHA-256",
            }
        ),
        hide_index=True,
        alt="Page and section passages with period, availability, and content hashes",
    )
    st.divider()
    st.subheader("Retrieval baseline lab")
    st.caption("Ranks eligible passages only. Retrieval scores do not verify an answer or a financial claim.")
    query = st.text_input(
        "Filing search query",
        "What warranty provision correction changed Alpha Industries net income?",
        key="filing_query",
    )
    method_label = st.radio(
        "Retrieval method",
        ["Lexical TF-IDF", "Dense LSA vectors"],
        horizontal=True,
        key="filing_retrieval_method",
    )
    method = "lexical" if method_label == "Lexical TF-IDF" else "dense_lsa"
    top_k = st.slider("Passages to return", 1, 8, 3, key="filing_top_k")
    if query.strip():
        ranked = rank_passages(eligible_passages, query, method=method, top_k=top_k)
        st.dataframe(
            ranked[["rank", "score", "passage_id", "company", "page", "section", "available_at", "text", "text_sha256"]]
            .rename(columns={
                "rank": "Rank", "score": "Score", "passage_id": "Passage ID", "company": "Company",
                "page": "Page", "section": "Section", "available_at": "Available at", "text": "Text",
                "text_sha256": "Passage SHA-256",
            }),
            hide_index=True,
            alt="Ranked filing passages with scores and source provenance",
        )

    st.subheader("Frozen retrieval diagnostic")
    cases = load_frozen_relevance_cases(str(RELEVANCE_CASES))
    summaries = []
    detail_frames = []
    for baseline in ("lexical", "dense_lsa"):
        summary, details = evaluate_retriever(passages, cases, baseline, top_k=3)
        summaries.append(summary)
        detail_frames.append(details)
    st.dataframe(
        pd.DataFrame(summaries).rename(columns={
            "method": "Method", "top_k": "K", "case_count": "Cases", "mean_recall_at_3": "Mean recall@3",
            "mean_reciprocal_rank": "MRR", "mean_ndcg_at_3": "Mean nDCG@3",
        }),
        hide_index=True,
        alt="Lexical and dense vector filing retrieval metrics on the frozen diagnostic",
    )
    with st.expander("Case-level retrieval evidence"):
        st.dataframe(
            pd.concat(detail_frames, ignore_index=True), hide_index=True,
            alt="Case-level lexical and dense filing retrieval ranks for the frozen diagnostic",
        )
    st.caption(
        f"Frozen authored cases: {len(cases)} · SHA-256 {file_sha256(RELEVANCE_CASES)} · "
        "fixture-author reviewed, not an external benchmark."
    )

    st.divider()
    st.subheader("Grounded filings answer")
    st.caption("Returns exact eligible source sentences with passage citations, or abstains. No generative model is used.")
    question = st.text_input(
        "Question for the eligible filings",
        "What amounts did Alpha's warranty correction change net income from and to?",
        key="filing_qa_question",
    )
    qa_result = answer_filing_question(passages, question, CUTOFFS[cutoff_label])
    if qa_result["status"] == "answered":
        st.success(qa_result["answer"])
        st.dataframe(
            pd.DataFrame(qa_result["citations"]).rename(columns={
                "passage_id": "Passage ID", "document_id": "Document ID", "company": "Company",
                "page": "Page", "section": "Section", "available_at": "Available at",
                "text_sha256": "Passage SHA-256", "quote": "Exact supporting quote",
            }),
            hide_index=True,
            alt="Exact filing answer citation with page section and passage hash",
        )
    else:
        st.info(qa_result["answer"])
    with st.expander("Answer audit"):
        st.json(qa_result["audit"])

    qa_cases = load_frozen_qa_cases(str(QA_CASES))
    qa_summary, qa_details = evaluate_filing_qa(passages, qa_cases)
    qa_cards = st.columns(4)
    qa_cards[0].metric("Status accuracy", f"{qa_summary['status_accuracy']:.1%}", border=True)
    qa_cards[1].metric("Citation accuracy", f"{qa_summary['citation_accuracy']:.1%}", border=True)
    qa_cards[2].metric("Token support", f"{qa_summary['numerical_token_support']:.1%}", border=True)
    qa_cards[3].metric("Abstention recall", f"{qa_summary['abstention_recall']:.1%}", border=True)
    with st.expander("Frozen QA case evidence"):
        st.dataframe(
            qa_details, hide_index=True,
            alt="Frozen filing question-answer cases with expected and observed citation and abstention outcomes",
        )
    st.caption(
        f"Frozen QA cases: {len(qa_cases)} · SHA-256 {file_sha256(QA_CASES)} · "
        "fixture-author reviewed mechanics, not real-world semantic validation."
    )
