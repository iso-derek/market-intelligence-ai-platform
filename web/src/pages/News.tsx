import { useEffect, useState, type ChangeEvent, type FormEvent } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Download, ExternalLink, RefreshCw, Search } from "lucide-react";
import { apiUrl, send, useApi } from "../api";
import { day, monthLabel, number, stamp } from "../format";
import { Block, Figure, Notice, PageHead, Sentiment, Skeleton, Tabs } from "../components/ui";

interface Headline {
  id: string; headline: string; source: string; url: string | null; published_at: string; available_at: string;
  company: string | null; ticker: string | null; sentiment: string; score: number; risk: string[];
}
interface NewsData {
  source: string; empty: boolean; synthetic: boolean; summary?: string;
  kpis: { headlines: number; sources: number; negative: number; positive: number; risk_flagged: number; average_tone: number } | null;
  monthly?: ({ month: string } & Record<string, number>)[];
  companies?: { company: string; headlines: number; tone: number }[];
  tickers?: string[];
  entities?: { resolved: number; ambiguous: number; unknown: number };
  events?: { classified: number; ambiguous: number; unknown: number; types: { type: string; count: number }[] };
  total: number; headlines: Headline[];
}
interface Brief {
  abstained: boolean; reason?: string; note?: string;
  claims: { text: string; url: string; source: string; published_at: string }[];
}
type Source = "demo" | "official" | "upload";

export default function News() {
  const [source, setSource] = useState<Source>("demo");
  const [uploadKey, setUploadKey] = useState<string>();
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [sentiment, setSentiment] = useState("");
  const [limit, setLimit] = useState(30);
  useEffect(() => {
    const timer = setTimeout(() => setQuery(search), 250);
    return () => clearTimeout(timer);
  }, [search]);
  const key = source === "upload" ? uploadKey : source;
  const news = useApi<NewsData>(key ? apiUrl("news", { source: key, search: query, sentiment, limit }) : null);
  const data = news.data;

  return (
    <>
      <PageHead kicker="News evidence" title="What the headlines are saying">
        Tone, companies and events across the latest headlines, with every claim linked back to its source.
      </PageHead>
      <div className="toolbar">
        <Tabs label="News source" value={source} onChange={(value) => { setSource(value); setLimit(30); }}
          options={[{ key: "demo", label: "Demo headlines" }, { key: "official", label: "Official feeds" }, { key: "upload", label: "Upload a file" }]} />
        {data && !data.empty && <span className="small muted">{number(data.total)} of {number(data.kpis?.headlines)} headlines shown</span>}
      </div>

      {source === "official" && <Sources onFetched={news.reload} />}
      {source === "upload" && <Upload onLoaded={setUploadKey} />}

      {news.error ? <Notice tone="warn">{news.error}</Notice> : !key ? null : !data ? <Skeleton height={420} /> : data.empty ? (
        <Notice>No headlines yet. {source === "official" ? "Enable a source and press Fetch to collect headlines." : "Upload a file to begin."}</Notice>
      ) : (
        <>
          {data.synthetic && <div style={{ marginBottom: 18 }}><Notice tone="warn">Demo headlines are generated examples. They show how the analysis works and are excluded from the evidence brief.</Notice></div>}
          <p className="lede">{data.summary}</p>
          <div className="grid cols-4 section" style={{ marginTop: 18 }}>
            <Figure label="Headlines" value={number(data.kpis!.headlines)} note={`From ${data.kpis!.sources} source${data.kpis!.sources === 1 ? "" : "s"}`} />
            <Figure label="Positive" value={number(data.kpis!.positive)} tone="pos" note="Upbeat wording" />
            <Figure label="Negative" value={number(data.kpis!.negative)} tone="neg" note="Downbeat wording" />
            <Figure label="Flag a risk" value={number(data.kpis!.risk_flagged)} note="e.g. layoffs, lawsuits, volatility" />
          </div>

          <div className="grid cols-main section">
            <Block title="Latest headlines" action={
              <div className="row">
                <label className="row" style={{ gap: 6 }}><Search size={16} aria-hidden className="muted" />
                  <input className="input" style={{ width: 200 }} placeholder="Search headlines" value={search} onChange={(event) => setSearch(event.target.value)} aria-label="Search headlines" />
                </label>
                <select className="input" style={{ width: "auto" }} value={sentiment} onChange={(event) => setSentiment(event.target.value)} aria-label="Tone">
                  <option value="">Any tone</option><option>Positive</option><option>Neutral</option><option>Negative</option>
                </select>
              </div>
            }>
              {data.headlines.length === 0 ? <p className="muted">No headlines match.</p> : data.headlines.map((item) => (
                <article key={item.id} className="story">
                  <h3>{item.url ? <a href={item.url} target="_blank" rel="noreferrer">{item.headline} <ExternalLink size={14} aria-hidden /></a> : item.headline}</h3>
                  <Sentiment value={item.sentiment} />
                  <div className="story-meta">
                    <span>{item.source}</span><span>·</span><span>{day(item.published_at)}</span>
                    {item.company && <><span>·</span><span>{item.company}</span></>}
                    {item.risk.map((flag) => <span key={flag} className="tag">{flag}</span>)}
                  </div>
                </article>
              ))}
              {data.total > data.headlines.length && (
                <button className="button section" type="button" style={{ marginTop: 16 }} onClick={() => setLimit(limit + 30)}>Show more headlines</button>
              )}
            </Block>

            <div className="stack" style={{ gap: 28 }}>
              <Block title="Tone by month">
                <div style={{ height: 220 }}>
                  <ResponsiveContainer>
                    <BarChart data={data.monthly} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
                      <CartesianGrid vertical={false} />
                      <XAxis dataKey="month" tickFormatter={monthLabel} tickLine={false} axisLine={false} />
                      <YAxis allowDecimals={false} tickLine={false} axisLine={false} />
                      <Tooltip labelFormatter={(label) => monthLabel(String(label))} cursor={{ fill: "var(--surface-2)" }} />
                      <Legend iconType="square" />
                      <Bar dataKey="Positive" stackId="t" fill="var(--pos)" />
                      <Bar dataKey="Neutral" stackId="t" fill="var(--neutral)" />
                      <Bar dataKey="Negative" stackId="t" fill="var(--neg)" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </Block>
              <Block title="Most mentioned">
                <table className="table">
                  <tbody>
                    {data.companies?.map((company) => (
                      <tr key={company.company}>
                        <td>{company.company}</td>
                        <td className="right">{company.headlines}</td>
                        <td className={`right ${company.tone > 0.05 ? "pos" : company.tone < -0.05 ? "neg" : "muted"}`}>
                          {company.tone > 0.05 ? "Upbeat" : company.tone < -0.05 ? "Downbeat" : "Mixed"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Block>
              <Block title="What kind of news" sub={`${data.events!.classified} headlines matched an event type; ${data.events!.ambiguous + data.events!.unknown} were unclear`}>
                <div className="stack" style={{ gap: 8 }}>
                  {data.events!.types.map((item) => (
                    <div key={item.type} className="row between small"><span>{item.type}</span><strong className="num">{item.count}</strong></div>
                  ))}
                </div>
              </Block>
            </div>
          </div>

          <EvidenceBrief source={key!} synthetic={data.synthetic} />
          <p className="small muted section">Tone describes the wording of a headline, not a prediction of returns. Company links use exact registered names only.</p>
        </>
      )}
    </>
  );
}

function EvidenceBrief({ source, synthetic }: { source: string; synthetic: boolean }) {
  const [question, setQuestion] = useState("interest rates");
  const [brief, setBrief] = useState<Brief>();
  const [busy, setBusy] = useState(false);
  const ask = async (event?: FormEvent) => {
    event?.preventDefault();
    setBusy(true);
    try {
      setBrief(await send<Brief>("/api/news/brief", "POST", { source, query: question }));
    } finally {
      setBusy(false);
    }
  };
  return (
    <Block title="Ask the evidence" className="section" sub="Returns the exact headlines that match, each linked to its source — or says there's nothing reliable."
      action={<a className="button" href={apiUrl("news/download", { source, query: question })}><Download size={16} aria-hidden /> Evidence bundle</a>}>
      {synthetic ? (
        <Notice>Switch to <strong>Official feeds</strong> or <strong>Upload a file</strong> to ask questions. Demo headlines can't be cited as evidence.</Notice>
      ) : (
        <>
          <form className="row" onSubmit={ask}>
            <input className="input" style={{ flex: 1, minWidth: 220 }} value={question} onChange={(event) => setQuestion(event.target.value)} aria-label="Question" />
            <button className="button button-primary" type="submit" disabled={busy}>{busy ? "Searching…" : "Find evidence"}</button>
          </form>
          {brief && (
            <div className="stack section" style={{ marginTop: 16 }}>
              {brief.abstained ? <Notice>{brief.reason}</Notice> : brief.claims.map((claim) => (
                <div key={claim.url + claim.text}>
                  <blockquote className="quote">{claim.text}</blockquote>
                  <div className="small muted" style={{ paddingLeft: 19 }}>{claim.source} · {day(claim.published_at)} · <a href={claim.url} target="_blank" rel="noreferrer">source</a></div>
                </div>
              ))}
              {brief.note && <p className="small muted">{brief.note}</p>}
            </div>
          )}
        </>
      )}
    </Block>
  );
}

interface SourceRow { source_id: string; name: string; feed_url: string; enabled: boolean; last_status: string | null; last_checked_at: string | null; last_error: string | null }

function Sources({ onFetched }: { onFetched: () => void }) {
  const list = useApi<{ sources: SourceRow[]; snapshots: number }>(apiUrl("sources"));
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string>();
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");

  const act = async (work: () => Promise<unknown>, done?: string) => {
    setBusy(true);
    setMessage(undefined);
    try {
      await work();
      if (done) setMessage(done);
      list.reload();
      onFetched();
    } catch (error) {
      setMessage((error as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Block title="Official sources" className="section" sub={list.data ? `${list.data.snapshots} saved snapshots · every fetch is stored exactly as received` : undefined}
      action={<button className="button button-primary" type="button" disabled={busy} onClick={() => act(() => send("/api/sources/fetch", "POST"), "Fetch finished.")}>
        <RefreshCw size={16} aria-hidden /> {busy ? "Working…" : "Fetch enabled sources"}
      </button>}>
      {message && <div style={{ marginBottom: 12 }}><Notice>{message}</Notice></div>}
      {!list.data ? <Skeleton height={120} /> : (
        <div className="scroll-x">
          <table className="table">
            <thead><tr><th>Use</th><th>Source</th><th>Last result</th><th>Checked</th></tr></thead>
            <tbody>
              {list.data.sources.map((row) => (
                <tr key={row.source_id}>
                  <td><input type="checkbox" checked={row.enabled} aria-label={`Use ${row.name}`}
                    onChange={(event) => act(() => send(`/api/sources/${row.source_id}`, "PATCH", { enabled: event.target.checked }))} /></td>
                  <td><strong>{row.name}</strong><div className="small muted" style={{ wordBreak: "break-all" }}>{row.feed_url}</div></td>
                  <td>{row.last_status ?? "Never fetched"}{row.last_error && <div className="small neg">{row.last_error}</div>}</td>
                  <td className="small muted">{stamp(row.last_checked_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <form className="row section" style={{ marginTop: 16 }} onSubmit={(event) => { event.preventDefault(); act(() => send("/api/sources", "POST", { name, url }), "Source added.").then(() => { setName(""); setUrl(""); }); }}>
        <input className="input" style={{ flex: "1 1 160px" }} placeholder="Source name" value={name} onChange={(event) => setName(event.target.value)} aria-label="Source name" required />
        <input className="input" style={{ flex: "2 1 260px" }} placeholder="https://… RSS or Atom feed" value={url} onChange={(event) => setUrl(event.target.value)} aria-label="Feed URL" required />
        <button className="button" type="submit" disabled={busy}>Add source</button>
      </form>
    </Block>
  );
}

function Upload({ onLoaded }: { onLoaded: (key: string) => void }) {
  const [message, setMessage] = useState<string>();
  const [busy, setBusy] = useState(false);
  const pick = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setBusy(true);
    setMessage(undefined);
    try {
      const result = await send<{ source: string; headlines: number }>("/api/news/upload", "POST", { csv: await file.text() });
      setMessage(`Loaded ${result.headlines} headlines from ${file.name}.`);
      onLoaded(result.source);
    } catch (error) {
      setMessage((error as Error).message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <Block title="Upload headlines" className="section" sub="A CSV with headline, published_at and url columns (source and available_at are optional). Kept in memory only.">
      <label className="button" style={{ cursor: busy ? "progress" : "pointer" }}>
        {busy ? "Reading…" : "Choose CSV file"}
        <input type="file" accept=".csv,text/csv" hidden onChange={pick} />
      </label>
      {message && <div style={{ marginTop: 12 }}><Notice>{message}</Notice></div>}
    </Block>
  );
}
