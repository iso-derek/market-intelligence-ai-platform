import { useEffect, useState } from "react";
import { ExternalLink } from "lucide-react";
import { apiUrl, useApi } from "../api";
import { day, percent, ratio } from "../format";
import { Block, Notice, PageHead, Skeleton } from "../components/ui";

interface Company {
  ticker: string; name: string; cik: number; latest_period: string | null; filed?: string;
  figures: Record<string, number>; ratios: { net_margin: number | null; current_ratio: number | null; debt_to_equity: number | null };
  history: { period_end: string; revenue?: number | null; net_income?: number | null }[];
  restatements: number; filings_url?: string;
}
interface CompaniesData {
  configured: boolean; message?: string; cutoff?: string; companies?: Company[]; problems?: string[]; source: string; source_url: string;
}

function billions(value: number | null | undefined): string {
  if (value == null) return "—";
  const abs = Math.abs(value);
  const text = abs >= 1e9 ? `$${(abs / 1e9).toFixed(1)}B` : `$${(abs / 1e6).toFixed(0)}M`;
  return value < 0 ? `−${text}` : text;
}

export default function Companies() {
  const today = new Date().toISOString().slice(0, 10);
  const [cutoff, setCutoff] = useState(today);
  const [input, setInput] = useState("AAPL, MSFT, JPM, WMT, XOM, JNJ");
  const [tickers, setTickers] = useState(input);
  useEffect(() => {
    const timer = setTimeout(() => setTickers(input), 600);
    return () => clearTimeout(timer);
  }, [input]);
  const { data, error, loading } = useApi<CompaniesData>(apiUrl("sec/companies", { tickers: tickers.replace(/\s/g, ""), cutoff }));

  return (
    <>
      <PageHead kicker="Company accounts" title="Real company accounts, as filed">
        Annual figures straight from companies' 10-K filings with the U.S. SEC. Pick a date to see the accounts exactly as they were known then
        — later corrections never leak into the past.
      </PageHead>
      <div className="toolbar">
        <input className="input" style={{ maxWidth: 360 }} value={input} onChange={(event) => setInput(event.target.value)} aria-label="Tickers"
          placeholder="Tickers, e.g. AAPL, MSFT" />
        <label className="row" style={{ gap: 8 }}>
          <span className="small muted">As known on</span>
          <input className="input" type="date" style={{ width: "auto" }} value={cutoff} max={today} onChange={(event) => setCutoff(event.target.value || today)} />
        </label>
      </div>

      {error ? <Notice tone="warn">{error}</Notice> : !data ? <Skeleton height={320} /> : !data.configured ? (
        <Block title="One step to switch this on">
          <p style={{ marginTop: 0 }}>
            The SEC asks every automated tool to say who is requesting its data, so this page needs your name and email set on the computer
            running the app. Nothing is requested from the SEC until you do.
          </p>
          <pre className="hash" style={{ background: "var(--surface-2)", padding: 12, whiteSpace: "pre-wrap" }}>
{`# Windows PowerShell
$env:SEC_USER_AGENT = "Your Name you@example.com"

# macOS / Linux
export SEC_USER_AGENT="Your Name you@example.com"`}
          </pre>
          <p className="small muted">Then restart the app. See the SEC's <a href="https://www.sec.gov/os/accessing-edgar-data" target="_blank" rel="noreferrer">fair-access policy</a>.</p>
        </Block>
      ) : (
        <div style={{ opacity: loading ? 0.5 : 1 }}>
          {data.problems && data.problems.length > 0 && <div style={{ marginBottom: 14 }}><Notice tone="warn">{data.problems.join(" ")}</Notice></div>}
          <Block title={`Latest annual accounts known on ${day(data.cutoff)}`} sub="Figures in US dollars from each company's most recent 10-K filed by that date">
            <div className="scroll-x">
              <table className="table">
                <thead>
                  <tr>
                    <th>Company</th><th>Year ending</th><th className="right">Revenue</th><th className="right">Net income</th>
                    <th className="right">Profit margin</th><th className="right">Bills cover</th><th className="right">Debt / equity</th><th />
                  </tr>
                </thead>
                <tbody>
                  {data.companies?.map((company) => (
                    <tr key={company.ticker}>
                      <td><strong>{company.name}</strong><div className="small muted">{company.ticker}{company.restatements > 0 ? ` · ${company.restatements} figure${company.restatements > 1 ? "s" : ""} later restated` : ""}</div></td>
                      <td>{company.latest_period ? day(company.latest_period) : "No 10-K yet"}{company.filed && <div className="small muted">filed {day(company.filed)}</div>}</td>
                      <td className="right">{billions(company.figures["Revenue"])}</td>
                      <td className={`right ${(company.figures["Net income"] ?? 0) < 0 ? "neg" : ""}`}>{billions(company.figures["Net income"])}</td>
                      <td className="right">{percent(company.ratios.net_margin)}</td>
                      <td className="right">{company.ratios.current_ratio == null ? "—" : `${ratio(company.ratios.current_ratio)}×`}</td>
                      <td className="right">{ratio(company.ratios.debt_to_equity)}</td>
                      <td>{company.filings_url && <a href={company.filings_url} target="_blank" rel="noreferrer" aria-label={`${company.name} filings`}><ExternalLink size={14} /></a>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="small muted">
              "Bills cover" is the current ratio: short-term assets divided by short-term debts. Some figures are missing when a company reports
              them under a different accounting label; banks, for example, don't report current assets.
            </p>
          </Block>
          <p className="small muted section">Source: <a href={data.source_url} target="_blank" rel="noreferrer">{data.source}</a> Not investment advice.</p>
        </div>
      )}
    </>
  );
}
