"""Streamlit presentation for the verified local filings corpus."""
from pathlib import Path

import pandas as pd
import streamlit as st

from filings import filings_as_of, load_filings_corpus


CORPUS_ROOT = Path(__file__).resolve().parents[1] / "data" / "filings"
CUTOFFS = {
    "23 January 2026 — Beta only": "2026-01-23T23:59:59Z",
    "1 February 2026 — Beta and Gamma": "2026-02-01T23:59:59Z",
    "1 March 2026 — all reports": "2026-03-01T23:59:59Z",
}


@st.cache_data
def load_verified_filings(root: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    return load_filings_corpus(root)


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
    st.caption("D4.1 verifies and displays the corpus only. Search, retrieval scoring, embeddings, and question answering are later milestones.")
