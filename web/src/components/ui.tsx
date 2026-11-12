import type { ReactNode } from "react";
import { AlertTriangle, Info } from "lucide-react";

export function PageHead({ kicker, title, children }: { kicker: string; title: string; children?: ReactNode }) {
  return (
    <header className="page-head">
      <div className="kicker">{kicker}</div>
      <h1>{title}</h1>
      {children && <p>{children}</p>}
    </header>
  );
}

export function Block({ title, sub, action, children, className = "" }: {
  title?: string; sub?: ReactNode; action?: ReactNode; children: ReactNode; className?: string;
}) {
  return (
    <section className={`block ${className}`}>
      {(title || action) && (
        <div className="block-head">
          <div>{title && <h2>{title}</h2>}{sub && <div className="block-sub">{sub}</div>}</div>
          {action}
        </div>
      )}
      {children}
    </section>
  );
}

export function Figure({ label, value, note, tone }: { label: string; value: ReactNode; note?: ReactNode; tone?: "pos" | "neg" }) {
  return (
    <div className="figure">
      <div className="figure-label">{label}</div>
      <div className={`figure-value ${tone ?? ""}`}>{value}</div>
      {note && <div className="figure-note">{note}</div>}
    </div>
  );
}

export function Tabs<T extends string>({ options, value, onChange, label }: {
  options: { key: T; label: string }[]; value: T; onChange: (value: T) => void; label: string;
}) {
  return (
    <div className="tabs" role="group" aria-label={label}>
      {options.map((option) => (
        <button key={option.key} type="button" aria-pressed={option.key === value} onClick={() => onChange(option.key)}>{option.label}</button>
      ))}
    </div>
  );
}

export function Notice({ tone = "info", children }: { tone?: "info" | "warn"; children: ReactNode }) {
  const Icon = tone === "warn" ? AlertTriangle : Info;
  return <div className={`notice ${tone === "warn" ? "notice-warn" : ""}`}><Icon size={18} style={{ flexShrink: 0, marginTop: 2 }} aria-hidden /><div>{children}</div></div>;
}

export function Skeleton({ height = 120 }: { height?: number }) {
  return <div className="skeleton" style={{ height }} role="status" aria-label="Loading" />;
}

export function Slider({ label, value, min, max, step, display, onChange }: {
  label: string; value: number; min: number; max: number; step: number; display: string; onChange: (value: number) => void;
}) {
  return (
    <label className="slider">
      <span className="slider-top"><span>{label}</span><strong>{display}</strong></span>
      <input type="range" min={min} max={max} step={step} value={value} onChange={(event) => onChange(Number(event.target.value))} />
    </label>
  );
}

export function Sentiment({ value }: { value: string }) {
  const tone = value === "Positive" ? "tag-pos" : value === "Negative" ? "tag-neg" : "";
  return <span className={`tag ${tone}`}>{value}</span>;
}

export function ViewPicker({ views, value, onChange }: { views: { key: string; label: string }[]; value: string; onChange: (value: string) => void }) {
  return (
    <label className="row" style={{ gap: 8 }}>
      <span className="small muted">As known on</span>
      <select className="input" style={{ width: "auto" }} value={value} onChange={(event) => onChange(event.target.value)}>
        {views.map((item) => <option key={item.key} value={item.key}>{item.label}</option>)}
      </select>
    </label>
  );
}
