import { useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { apiUrl, useApi } from "../api";
import { day, number, percent, rate, ratio, shortDay } from "../format";
import { Block, Figure, Notice, PageHead, Skeleton, Tabs, ViewPicker } from "../components/ui";

interface MarketsData {
  views: { key: string; label: string }[]; view: string; cutoff: string; instrument: string;
  companies: { key: string; label: string }[];
  headline: { name: string; close: number; currency: string; return: number; volatility: number; exchange: string; latest: string };
  prices: { date: string; raw: number; adjusted: number }[];
  universe: { ticker: string; name: string; close: number; currency: string; return: number; volatility: number; days: number }[];
  macro: {
    latest: { id: string; name: string; value: number; unit: string; period: string; available_at: string }[];
    history: { id: string; name: string; period: string; value: number; unit: string; released: string; vintage: string; available_at: string }[];
  };
  peers: { ticker: string; name: string; sector: string; revenue: number; net_income: number; net_margin: number; current_ratio: number; debt_to_equity: number; currency: string; unit: string; version: number }[];
  facts: { metric: string; value: number; currency: string; unit: string; version: number; filed: string }[];
  rates: {
    curve: { name: string; tenor: string; value: number }[];
    spreads: { name: string; tenor: string; yield: number; benchmark: string; benchmark_yield: number; spread_bps: number }[];
    fx: { pair: string; unit: string; first: number; latest: number; return: number; meaning: string }[];
  };
}
interface EventData { session: string; car: number; peers: number; window: { day: number; date: string; instrument: number; benchmark: number; abnormal: number; cumulative: number }[] }

export default function Markets() {
  const [viewKey, setViewKey] = useState("revised");
  const [instrument, setInstrument] = useState("ALP");
  const [release, setRelease] = useState("2026-01-06T14:00:00Z");
  const { data, error } = useApi<MarketsData>(apiUrl("markets", { view: viewKey, instrument }));
  const event = useApi<EventData>(apiUrl("markets/event", { view: viewKey, instrument, release }));
  if (error) return <Notice tone="warn">{error}</Notice>;
  if (!data) return <Skeleton height={480} />;
  const h = data.headline;

  return (
    <>
      <PageHead kicker="Markets & macro" title={`${h.name} and the wider picture`}>
        Prices, economic data and company accounts exactly as they were known on a chosen date, so later revisions can't leak in.
      </PageHead>
      <div className="toolbar">
        <Tabs label="Company" value={instrument} onChange={setInstrument} options={data.companies} />
        <ViewPicker views={data.views} value={viewKey} onChange={setViewKey} />
      </div>
      <Notice>These are small, fictional teaching datasets, not live prices or advice.</Notice>

      <div className="grid cols-4 section">
        <Figure label="Latest close" value={`${number(h.close, 2)} ${h.currency}`} note={`${day(h.latest)} · ${h.exchange}`} />
        <Figure label="Return over the period" value={percent(h.return, 1, true)} tone={h.return >= 0 ? "pos" : "neg"} />
        <Figure label="Volatility" value={percent(h.volatility)} note="Yearly swing in price" />
        <Figure label="Trading days" value={data.universe.find((item) => item.ticker === instrument)?.days ?? "—"} />
      </div>

      <div className="grid cols-main section">
        <Block title="Share price" sub="The adjusted line removes the effect of the stock split, so returns stay comparable">
          <div style={{ height: 280 }}>
            <ResponsiveContainer>
              <LineChart data={data.prices} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                <CartesianGrid vertical={false} />
                <XAxis dataKey="date" tickFormatter={shortDay} tickLine={false} axisLine={false} />
                <YAxis width={44} tickLine={false} axisLine={false} domain={["auto", "auto"]} />
                <Tooltip labelFormatter={(label) => day(String(label))} formatter={(value) => number(Number(value), 2)} />
                <Legend iconType="plainline" />
                <Line dataKey="adjusted" name="Adjusted close" stroke="var(--accent)" strokeWidth={2.5} dot />
                <Line dataKey="raw" name="Raw close" stroke="var(--faint)" strokeDasharray="4 4" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Block>
        <Block title="The three companies">
          <table className="table">
            <thead><tr><th>Company</th><th className="right">Return</th><th className="right">Volatility</th></tr></thead>
            <tbody>
              {data.universe.map((row) => (
                <tr key={row.ticker} style={row.ticker === instrument ? { background: "var(--accent-soft)" } : undefined}>
                  <td>{row.name}</td>
                  <td className={`right ${row.return >= 0 ? "pos" : "neg"}`}>{percent(row.return, 1, true)}</td>
                  <td className="right">{percent(row.volatility)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Block>
      </div>

      <div className="grid cols-2 section">
        <Block title="The economy" sub="Latest reading of each indicator known by this date">
          <div className="grid cols-2" style={{ gap: 16 }}>
            {data.macro.latest.map((item) => (
              <Figure key={item.id} label={item.name} value={`${rate(item.value)}${item.unit.startsWith("percent") ? "%" : ""}`}
                note={`${item.unit.replace(/^percent\s*/, "") || "Rate"} · for ${new Date(item.period).toLocaleDateString("en-US", { month: "long", year: "numeric", timeZone: "UTC" })}`} />
            ))}
          </div>
          <p className="small muted">Try switching the date: December inflation was first published as 2.9% and later revised to 3.0%.</p>
        </Block>
        <Block title="Interest rates & currencies">
          <table className="table">
            <tbody>
              {data.rates.curve.map((row) => <tr key={row.name}><td>{row.name} government bond yield</td><td className="right">{number(row.value, 2)}%</td></tr>)}
              {data.rates.spreads.map((row) => <tr key={row.name}><td>{row.name} extra yield over {row.benchmark}</td><td className="right">{number(row.spread_bps)} bps</td></tr>)}
              {data.rates.fx.map((row) => <tr key={row.pair}><td>{row.meaning}</td><td className={`right ${row.return >= 0 ? "pos" : "neg"}`}>{percent(row.return, 1, true)}</td></tr>)}
            </tbody>
          </table>
          {data.rates.fx.length === 0 && <p className="small muted">Currency data wasn't available yet on this date.</p>}
        </Block>
      </div>

      <Block title="Company accounts compared" className="section" sub={`Figures in ${data.peers[0]?.currency ?? ""} ${data.peers[0]?.unit ?? ""} · from the latest report available on this date`}>
        <div className="scroll-x">
          <table className="table">
            <thead><tr><th>Company</th><th>Sector</th><th className="right">Revenue</th><th className="right">Net income</th><th className="right">Profit margin</th><th className="right">Can cover short-term bills</th><th className="right">Debt per $ of equity</th></tr></thead>
            <tbody>
              {data.peers.map((row) => (
                <tr key={row.ticker}>
                  <td><strong>{row.name}</strong>{row.version > 1 && <span className="tag tag-accent" style={{ marginLeft: 8 }}>Restated</span>}</td>
                  <td>{row.sector}</td><td className="right">{number(row.revenue)}</td><td className="right">{number(row.net_income)}</td>
                  <td className="right">{percent(row.net_margin)}</td><td className="right">{ratio(row.current_ratio)}×</td><td className="right">{ratio(row.debt_to_equity)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="small muted">"Can cover short-term bills" is the current ratio: short-term assets divided by short-term debts. Above 1 is comfortable.</p>
      </Block>

      <div className="grid cols-2 section">
        <Block title={`${h.name}: report details`} sub="One complete report version is used — never a mix of old and restated figures">
          <table className="table">
            <tbody>
              {data.facts.map((fact) => <tr key={fact.metric}><td>{fact.metric}</td><td className="right">{number(fact.value)} {fact.currency} {fact.unit}</td></tr>)}
            </tbody>
          </table>
          {data.facts[0] && <p className="small muted">Report version {data.facts[0].version}, filed {day(data.facts[0].filed)}.</p>}
        </Block>
        <Block title="How the price reacted to news" sub="Return beyond what similar companies did, the day before, of and after a release"
          action={<Tabs label="Release time" value={release} onChange={setRelease}
            options={[{ key: "2026-01-06T14:00:00Z", label: "During trading" }, { key: "2026-01-05T22:00:00Z", label: "After the close" }]} />}>
          {event.error ? <Notice tone="warn">{event.error}</Notice> : !event.data ? <Skeleton height={200} /> : (
            <>
              <div className="row" style={{ gap: 28, marginBottom: 8 }}>
                <Figure label="Extra return over 3 days" value={percent(event.data.car, 2, true)} tone={event.data.car >= 0 ? "pos" : "neg"} />
                <Figure label="Counted from" value={shortDay(event.data.session)} note={`Compared with ${event.data.peers} peers`} />
              </div>
              <div style={{ height: 160 }}>
                <ResponsiveContainer>
                  <BarChart data={event.data.window.map((row) => ({ ...row, label: row.day === 0 ? "Release day" : row.day < 0 ? "Day before" : "Day after" }))} margin={{ top: 4, right: 4, bottom: 0, left: -10 }}>
                    <CartesianGrid vertical={false} />
                    <XAxis dataKey="label" tickLine={false} axisLine={false} />
                    <YAxis tickFormatter={(value) => percent(value, 1)} tickLine={false} axisLine={false} />
                    <Tooltip formatter={(value) => percent(Number(value), 2, true)} cursor={{ fill: "var(--surface-2)" }} />
                    <Bar dataKey="abnormal" name="Extra return">
                      {event.data.window.map((row) => <Cell key={row.day} fill={row.abnormal >= 0 ? "var(--pos)" : "var(--neg)"} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <p className="small muted">A tiny teaching example of the arithmetic — it can't prove the news caused the move.</p>
            </>
          )}
        </Block>
      </div>
    </>
  );
}
