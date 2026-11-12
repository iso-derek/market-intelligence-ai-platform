import { useState } from "react";
import { ArrowRight } from "lucide-react";
import { apiUrl, useApi } from "../api";
import { day, percent } from "../format";
import { Block, Figure, Notice, PageHead, Skeleton, ViewPicker } from "../components/ui";

interface GraphData {
  views: { key: string; label: string }[]; view: string; hash: string;
  nodes: { id: string; type: string; label: string; available_at: string }[];
  edges: { id: string; from: string; to: string; relationship: string; available_at: string }[];
  paths: Record<string, unknown>[];
  evaluation: { graph_exact_rate: number; table_exact_rate: number; method_parity_rate: number; inspection_reduction: number; conclusion: string };
}
interface OperationsData {
  health: { status: string; sources?: number; attempts?: number; failed_attempts?: number; schema_version?: number; latest_attempt_at?: string | null };
}

export default function Evidence() {
  const [viewKey, setViewKey] = useState("mar");
  const { data, error } = useApi<GraphData>(apiUrl("graph", { view: viewKey }));
  const ops = useApi<OperationsData>(apiUrl("operations"));
  if (error) return <Notice tone="warn">{error}</Notice>;
  if (!data) return <Skeleton height={420} />;
  const label = Object.fromEntries(data.nodes.map((node) => [node.id, node.label]));
  const type = Object.fromEntries(data.nodes.map((node) => [node.id, node.type]));

  return (
    <>
      <PageHead kicker="Evidence & operations" title="Follow every number back to its source">
        A map of how companies, reports, passages and figures link together — showing provenance, not cause and effect — plus the health of
        the local evidence store.
      </PageHead>
      <div className="toolbar">
        <span className="small muted">{data.nodes.length} items · {data.edges.length} links</span>
        <ViewPicker views={data.views} value={viewKey} onChange={setViewKey} />
      </div>

      <Block title="The evidence trail" sub="Starting from Alpha Industries">
        {data.edges.length === 0 ? <p className="muted">No links were known by this date.</p> : (
          <div className="stack" style={{ gap: 10 }}>
            {data.edges.map((edge) => (
              <div key={edge.id} className="row" style={{ gap: 10, padding: "8px 0", borderBottom: "1px solid var(--rule)" }}>
                <span><span className="tag">{type[edge.from]}</span> <strong>{label[edge.from] ?? edge.from}</strong></span>
                <span className="row small muted" style={{ gap: 4 }}><ArrowRight size={14} aria-hidden />{edge.relationship.toLowerCase()}<ArrowRight size={14} aria-hidden /></span>
                <span><span className="tag">{type[edge.to]}</span> <strong>{label[edge.to] ?? edge.to}</strong></span>
                <span className="small muted" style={{ marginLeft: "auto" }}>known from {day(edge.available_at)}</span>
              </div>
            ))}
          </div>
        )}
      </Block>

      <Block title="Is the map worth it?" className="section" sub="The same questions answered by following the map versus scanning a plain table">
        <div className="grid cols-4">
          <Figure label="Map answers exactly right" value={percent(data.evaluation.graph_exact_rate, 0)} />
          <Figure label="Table answers exactly right" value={percent(data.evaluation.table_exact_rate, 0)} />
          <Figure label="Both agree" value={percent(data.evaluation.method_parity_rate, 0)} />
          <Figure label="Fewer rows to inspect" value={percent(data.evaluation.inspection_reduction, 0)} />
        </div>
        <p className="small muted">{data.evaluation.conclusion}</p>
      </Block>

      <Block title="Evidence store health" className="section">
        {!ops.data ? <Skeleton height={80} /> : ops.data.health.status !== "healthy" ? (
          <Notice>The local evidence store hasn't been set up yet. Open News → Official feeds once to create it.</Notice>
        ) : (
          <div className="grid cols-4">
            <Figure label="Status" value="Healthy" tone="pos" note={`Format version ${ops.data.health.schema_version}`} />
            <Figure label="Registered sources" value={ops.data.health.sources ?? 0} />
            <Figure label="Fetches" value={ops.data.health.attempts ?? 0} note={ops.data.health.latest_attempt_at ? `Latest ${day(ops.data.health.latest_attempt_at)}` : "None yet"} />
            <Figure label="Failed fetches" value={ops.data.health.failed_attempts ?? 0} tone={(ops.data.health.failed_attempts ?? 0) > 0 ? "neg" : undefined} />
          </div>
        )}
        <p className="small muted">Single-user local storage. Backups, encryption and off-site copies are up to the owner.</p>
        <p className="small muted">Map fingerprint: <span className="hash">{data.hash}</span></p>
      </Block>
    </>
  );
}
