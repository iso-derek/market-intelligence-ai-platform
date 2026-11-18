import { useEffect, useState } from "react";
import { Check, Download, Save, X } from "lucide-react";
import { apiUrl, send, useApi } from "../api";
import { day, stamp, withUnit } from "../format";
import { Block, Figure, Notice, PageHead, Skeleton, Slider, Tabs, ViewPicker } from "../components/ui";

interface Fact { fact_key: string; label: string; value: number; unit: string }
interface WorkflowData {
  views: { key: string; label: string }[]; companies: { key: string; label: string }[];
  status: string; budget: { max_steps: number; steps_used: number; max_seconds: number }; artifact_hash: string; question: string;
  trace: { step: number; role: string; tool: string; status: string; message: string; facts: Fact[]; citations: number }[];
  report: {
    claims: { claim_id: string; fact_key: string; label: string; value: number; unit: string; statement: string; citations: { evidence_id: string; uri: string; available_at: string }[] }[];
    reconciliation: { fact_key: string; report_value: number; source_value: number; report_unit: string; value_match: boolean; unit_match: boolean }[];
    hash: string; limitations: string | string[];
  };
}
interface Run { id: string; recorded_at: string; as_of: string; company: string; status: string }
const STATUS_COLOR: Record<string, string> = { success: "var(--pos)", missing: "#c99400", conflict: "var(--neg)", failed: "var(--neg)" };
const STATUS_TEXT: Record<string, string> = { success: "Done", missing: "No data available", conflict: "Sources disagree", failed: "Failed" };

export default function Research() {
  const [company, setCompany] = useState("ALP");
  const [viewKey, setViewKey] = useState("revised");
  const [question, setQuestion] = useState("");
  const [asked, setAsked] = useState("");
  const [seconds, setSeconds] = useState(5);
  const { data, error } = useApi<WorkflowData>(apiUrl("workflow", { company, view: viewKey, question: asked, max_seconds: seconds }));
  const runs = useApi<{ runs: Run[] }>(apiUrl("workflow/runs"));
  const [saveMessage, setSaveMessage] = useState<string>();
  const [base, setBase] = useState("");
  const [target, setTarget] = useState("");
  const comparison = useApi<{ rows: { metric: string; base: unknown; target: unknown; change: string }[]; limitations: string }>(
    base && target && base !== target ? apiUrl("workflow/compare", { base, target }) : null,
  );
  useEffect(() => {
    const list = runs.data?.runs ?? [];
    if (list.length >= 2 && !base) { setTarget(list[0].id); setBase(list[1].id); }
  }, [runs.data, base]);

  const save = async () => {
    try {
      const result = await send<{ run: string; created: boolean }>("/api/workflow/runs", "POST", { company, view: viewKey, question: asked, max_seconds: seconds });
      setSaveMessage(result.created ? "Saved. Runs can't be edited afterwards." : "This exact run was already saved — nothing was duplicated.");
      runs.reload();
    } catch (problem) {
      setSaveMessage((problem as Error).message);
    }
  };

  return (
    <>
      <PageHead kicker="Research desk" title="A research note, built step by step">
        Five specialist steps gather company figures, the economy and risks, then a summary that cites every number. Each figure is checked
        against its source.
      </PageHead>
      <div className="toolbar">
        <Tabs label="Company" value={company} onChange={setCompany} options={data?.companies ?? [{ key: "ALP", label: "Alpha Industries" }]} />
        {data && <ViewPicker views={data.views} value={viewKey} onChange={setViewKey} />}
      </div>
      <div className="grid cols-main">
        <div className="row">
          <input className="input" style={{ flex: 1, minWidth: 240 }} placeholder={`What is the evidence-backed outlook and risk context for ${company}?`}
            value={question} onChange={(event) => setQuestion(event.target.value)} onKeyDown={(event) => event.key === "Enter" && setAsked(question)} aria-label="Research question" />
          <button className="button button-primary" type="button" onClick={() => setAsked(question)}>Run</button>
        </div>
        <Slider label="Time limit" value={seconds} min={1} max={10} step={1} display={`${seconds} s`} onChange={setSeconds} />
      </div>

      {error ? <Notice tone="warn">{error}</Notice> : !data ? <Skeleton height={420} /> : (
        <>
          <div className="grid cols-4 section">
            <Figure label="Result" value={data.status === "complete" ? "Complete" : data.status} />
            <Figure label="Steps used" value={`${data.budget.steps_used} of ${data.budget.max_steps}`} />
            <Figure label="Gaps" value={data.trace.filter((step) => step.status === "missing").length} note="Steps with no data" />
            <Figure label="Disagreements" value={data.trace.filter((step) => step.status === "conflict").length} />
          </div>

          <div className="grid cols-2 section">
            <Block title="The steps">
              {data.trace.map((step) => (
                <div key={step.step} className="step">
                  <span className="step-dot" style={{ background: STATUS_COLOR[step.status] ?? "var(--faint)" }}>{step.step}</span>
                  <div>
                    <div className="row between"><strong>{step.role}</strong><span className="small" style={{ color: STATUS_COLOR[step.status] }}>{STATUS_TEXT[step.status] ?? step.status}</span></div>
                    <div className="small muted">{step.message || step.tool}</div>
                    {step.facts.map((fact) => (
                      <div key={fact.fact_key} className="small">{fact.label}: <strong>{withUnit(fact.value, fact.unit)}</strong></div>
                    ))}
                  </div>
                </div>
              ))}
              <p className="small muted">The news step is deliberately offline in this demo, and the gap stays visible instead of being hidden.</p>
            </Block>
            <Block title="The note" action={<a className="button" href={apiUrl("workflow/report", { company, view: viewKey, question: asked })}><Download size={16} aria-hidden /> Download</a>}>
              {data.report.claims.map((claim) => {
                const check = data.report.reconciliation.find((row) => row.fact_key === claim.fact_key);
                const ok = check ? check.value_match && check.unit_match : true;
                return (
                  <div key={claim.claim_id} className="passage">
                    <div className="row between">
                      <span style={{ fontFamily: "var(--serif)", fontSize: 18 }}>{claim.label}: {withUnit(claim.value, claim.unit)}</span>
                      <span className={`row small ${ok ? "pos" : "neg"}`} style={{ gap: 4 }}>{ok ? <Check size={14} /> : <X size={14} />}{ok ? "Matches source" : "Mismatch"}</span>
                    </div>
                    {claim.citations.map((citation) => (
                      <div key={citation.evidence_id} className="small muted">Source: {citation.uri.replace("repo://", "")} · available {day(citation.available_at)}</div>
                    ))}
                  </div>
                );
              })}
              <p className="small muted">A complete set of steps doesn't make the research good, and no investment recommendation is made.</p>
              <p className="small muted">Note fingerprint: <span className="hash">{data.report.hash}</span></p>
            </Block>
          </div>

          <Block title="Saved runs" className="section" sub="Save a run to compare it later — for example, the same company before and after the revisions."
            action={<button className="button" type="button" onClick={save}><Save size={16} aria-hidden /> Save this run</button>}>
            {saveMessage && <div style={{ marginBottom: 12 }}><Notice>{saveMessage}</Notice></div>}
            {!runs.data ? <Skeleton height={80} /> : runs.data.runs.length === 0 ? <p className="muted">No runs saved yet.</p> : (
              <>
                <table className="table">
                  <thead><tr><th>Saved</th><th>Company</th><th>As known on</th><th>Result</th></tr></thead>
                  <tbody>{runs.data.runs.map((run) => (
                    <tr key={run.id}><td>{stamp(run.recorded_at)}</td><td>{run.company}</td><td>{day(run.as_of)}</td><td>{run.status}</td></tr>
                  ))}</tbody>
                </table>
                {runs.data.runs.length >= 2 && (
                  <div className="section" style={{ marginTop: 18 }}>
                    <div className="row">
                      <span className="small muted">Compare</span>
                      <select className="input" style={{ width: "auto" }} value={base} onChange={(event) => setBase(event.target.value)} aria-label="Earlier run">
                        {runs.data.runs.map((run) => <option key={run.id} value={run.id}>{run.company} · {stamp(run.recorded_at)}</option>)}
                      </select>
                      <span className="small muted">with</span>
                      <select className="input" style={{ width: "auto" }} value={target} onChange={(event) => setTarget(event.target.value)} aria-label="Later run">
                        {runs.data.runs.map((run) => <option key={run.id} value={run.id}>{run.company} · {stamp(run.recorded_at)}</option>)}
                      </select>
                    </div>
                    {comparison.data && (
                      <table className="table" style={{ marginTop: 12 }}>
                        <thead><tr><th>What</th><th>First</th><th>Second</th><th>Change</th></tr></thead>
                        <tbody>{comparison.data.rows.map((row) => (
                          <tr key={row.metric}><td>{row.metric.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase())}</td><td className="small">{String(row.base)}</td><td className="small">{String(row.target)}</td>
                            <td className={row.change === "unchanged" ? "muted" : ""}>{row.change}</td></tr>
                        ))}</tbody>
                      </table>
                    )}
                  </div>
                )}
              </>
            )}
          </Block>
        </>
      )}
    </>
  );
}
