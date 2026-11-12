import { useEffect, useState, type FormEvent } from "react";
import { CheckCircle2, FileText } from "lucide-react";
import { apiUrl, send, useApi } from "../api";
import { day, number, percent } from "../format";
import { Block, Figure, Notice, PageHead, Skeleton, Tabs, ViewPicker } from "../components/ui";

interface Passage { id: string; document: string; company: string; page: number; section: string; text: string; available_at: string; hash: string; rank?: number; score?: number }
interface FilingsData {
  views: { key: string; label: string }[]; view: string;
  documents: { id: string; company: string; ticker: string; form: string; period_end: string; filed: string; available_at: string; pages: number; sections: number; verified: boolean; hash: string }[];
  passages: Passage[];
}
interface Answer {
  status: string; answer: string;
  citations: { passage_id: string; company: string; page: number; section: string; quote: string; available_at: string }[];
}
interface Evaluation {
  retrieval: { method: string; case_count: number; mean_recall_at_3: number; mean_reciprocal_rank: number; mean_ndcg_at_3: number }[];
  qa: { case_count: number; status_accuracy: number; citation_accuracy: number; numerical_token_support: number; abstention_recall: number };
}

export default function Filings() {
  const [viewKey, setViewKey] = useState("all");
  const [documentId, setDocumentId] = useState<string>();
  const [question, setQuestion] = useState("What amounts did Alpha's warranty correction change net income from and to?");
  const [answer, setAnswer] = useState<Answer>();
  const [asking, setAsking] = useState(false);
  const [search, setSearch] = useState("warranty provision net income");
  const [method, setMethod] = useState<"lexical" | "dense_lsa">("lexical");
  const { data, error } = useApi<FilingsData>(apiUrl("filings", { view: viewKey }));
  const results = useApi<{ results: Passage[] }>(search.trim() ? apiUrl("filings/search", { q: search, method, top_k: 3, view: viewKey }) : null);
  const evaluation = useApi<Evaluation>(apiUrl("filings/evaluation"));
  useEffect(() => {
    if (data && !data.documents.some((doc) => doc.id === documentId)) setDocumentId(data.documents[0]?.id);
  }, [data, documentId]);

  const ask = async (event?: FormEvent) => {
    event?.preventDefault();
    setAsking(true);
    try {
      setAnswer(await send<Answer>(apiUrl("filings/answer", { q: question, view: viewKey })));
    } finally {
      setAsking(false);
    }
  };
  useEffect(() => { ask(); }, [viewKey]); // eslint-disable-line react-hooks/exhaustive-deps

  if (error) return <Notice tone="warn">{error}</Notice>;
  if (!data) return <Skeleton height={480} />;
  const doc = data.documents.find((item) => item.id === documentId);

  return (
    <>
      <PageHead kicker="Filings" title="Ask the annual reports">
        Questions are answered only with exact sentences from reports published by the chosen date — with page references — or the app says it
        can't answer.
      </PageHead>
      <div className="toolbar">
        <span className="small muted">{data.documents.length} report{data.documents.length === 1 ? "" : "s"} available · every file's fingerprint verified</span>
        <ViewPicker views={data.views} value={viewKey} onChange={setViewKey} />
      </div>

      <Block title="Ask a question">
        <form className="row" onSubmit={ask}>
          <input className="input" style={{ flex: 1, minWidth: 260 }} value={question} onChange={(event) => setQuestion(event.target.value)} aria-label="Question about the reports" />
          <button className="button button-primary" type="submit" disabled={asking}>{asking ? "Reading…" : "Answer"}</button>
        </form>
        {answer && (
          <div className="section" style={{ marginTop: 18 }}>
            {answer.status === "answered" ? (
              <>
                <blockquote className="quote">{answer.answer}</blockquote>
                {answer.citations.map((citation) => (
                  <p key={citation.passage_id} className="small muted" style={{ paddingLeft: 19 }}>
                    {citation.company} annual report · page {citation.page} · {citation.section} · published {day(citation.available_at)}
                  </p>
                ))}
              </>
            ) : <Notice>{answer.answer}</Notice>}
          </div>
        )}
      </Block>

      <div className="grid cols-main section">
        <Block title="Read a report" action={
          <Tabs label="Report" value={documentId ?? ""} onChange={setDocumentId} options={data.documents.map((item) => ({ key: item.id, label: item.company }))} />
        }>
          {!doc ? <p className="muted">No report had been published by this date.</p> : (
            <>
              <div className="row small muted" style={{ marginBottom: 6 }}>
                <FileText size={16} aria-hidden /> {doc.form} for the period to {day(doc.period_end)} · filed {day(doc.filed)} · {doc.pages} pages
                {doc.verified && <span className="row pos" style={{ gap: 4 }}><CheckCircle2 size={14} aria-hidden /> fingerprint verified</span>}
              </div>
              {data.passages.filter((passage) => passage.document === doc.id).map((passage) => (
                <div key={passage.id} className="passage">
                  <div className="small muted">Page {passage.page} · <strong style={{ color: "var(--ink)" }}>{passage.section}</strong></div>
                  <p>{passage.text}</p>
                </div>
              ))}
            </>
          )}
        </Block>
        <Block title="Search the reports" sub="Finds the most relevant passages. A match isn't proof of an answer.">
          <div className="stack">
            <input className="input" value={search} onChange={(event) => setSearch(event.target.value)} aria-label="Search the reports" />
            <Tabs label="Search method" value={method} onChange={setMethod} options={[{ key: "lexical", label: "Keyword match" }, { key: "dense_lsa", label: "Meaning match" }]} />
            {results.data?.results.map((passage) => (
              <div key={passage.id} className="passage">
                <div className="row between small"><strong>#{passage.rank} · {passage.company}, p.{passage.page}</strong><span className="muted">score {number(passage.score, 2)}</span></div>
                <p className="small">{passage.text}</p>
              </div>
            ))}
            {results.data && results.data.results.length === 0 && <p className="muted small">No passages found.</p>}
          </div>
        </Block>
      </div>

      {evaluation.data && (
        <Block title="How reliable is this?" className="section" sub={`Tested on ${evaluation.data.qa.case_count} prepared questions — including ones that should be refused`}>
          <div className="grid cols-4">
            <Figure label="Right decision to answer or refuse" value={percent(evaluation.data.qa.status_accuracy, 0)} />
            <Figure label="Cites the right passage" value={percent(evaluation.data.qa.citation_accuracy, 0)} />
            <Figure label="Numbers backed by the source" value={percent(evaluation.data.qa.numerical_token_support, 0)} />
            <Figure label="Refuses when it should" value={percent(evaluation.data.qa.abstention_recall, 0)} />
          </div>
          <p className="small muted">These are small, author-written checks of the mechanics, not an independent benchmark.</p>
        </Block>
      )}
    </>
  );
}
