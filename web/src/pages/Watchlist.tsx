import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { apiUrl, useApi } from "../api";
import { SERIES, day, number, percent, ratio, shortDay } from "../format";
import { Block, Figure, Notice, PageHead, Skeleton, Slider, Tabs, ViewPicker } from "../components/ui";

interface Company { ticker: string; name: string; sector: string; aliases: string }
interface Snapshot {
  ticker: string; name: string; sector: string; close: number; currency: string; return: number; volatility: number; revenue: number;
  net_income: number; net_margin: number; current_ratio: number; debt_to_equity: number; unit: string; price_source: string;
  filing_source: string; price_available_at: string; filing_available_at: string;
}
interface Preset { revenue_shock: number; margin_shock_bps: number; current_assets_shock: number; current_liabilities_shock: number; debt_shock: number; equity_shock: number }
interface WatchlistData {
  views: { key: string; label: string }[]; universe: Company[]; sectors: string[]; matches: string[]; selected: string[];
  presets: Record<string, Preset>; snapshot: Snapshot[]; indexed: ({ date: string } & Record<string, number>)[]; identity: string | null;
}
interface StressRow {
  ticker: string; name: string; net_income: number; stressed_net_income: number; change: number; net_margin: number; stressed_net_margin: number;
  current_ratio: number; stressed_current_ratio: number; debt_to_equity: number; stressed_debt_to_equity: number;
}
interface Shocks { revenue: number; margin_bps: number; assets: number; liabilities: number; debt: number; equity: number }

const fromPreset = (preset: Preset): Shocks => ({
  revenue: preset.revenue_shock, margin_bps: preset.margin_shock_bps, assets: preset.current_assets_shock,
  liabilities: preset.current_liabilities_shock, debt: preset.debt_shock, equity: preset.equity_shock,
});

function best<T>(rows: T[], pick: (row: T) => number, highest = true): T | undefined {
  return [...rows].sort((a, b) => (highest ? pick(b) - pick(a) : pick(a) - pick(b)))[0];
}

export default function Watchlist() {
  const [viewKey, setViewKey] = useState("revised");
  const [selected, setSelected] = useState<string[]>(() => {
    try {
      return JSON.parse(localStorage.getItem("signal-watchlist") ?? "null") ?? ["ALP", "BET", "GAM"];
    } catch {
      return ["ALP", "BET", "GAM"];
    }
  });
  const [search, setSearch] = useState("");
  const [sectors, setSectors] = useState<string[]>([]);
  const [presetName, setPresetName] = useState("Downside");
  const [shocks, setShocks] = useState<Shocks>({ revenue: -0.1, margin_bps: -300, assets: -0.1, liabilities: 0.1, debt: 0.2, equity: -0.1 });
  const [debounced, setDebounced] = useState(shocks);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(shocks), 150);
    return () => clearTimeout(timer);
  }, [shocks]);
  useEffect(() => {
    try { localStorage.setItem("signal-watchlist", JSON.stringify(selected)); } catch { /* ignore */ }
  }, [selected]);

  const { data, error } = useApi<WatchlistData>(apiUrl("watchlist", { view: viewKey, tickers: selected.join(","), q: search, sectors: sectors.join(",") }));
  const stress = useApi<{ unit: string; identity: string; rows: StressRow[] }>(
    selected.length ? apiUrl("watchlist/stress", { view: viewKey, tickers: selected.join(","), ...debounced }) : null,
  );
  const toggle = (ticker: string) => setSelected((list) => (list.includes(ticker) ? list.filter((item) => item !== ticker) : [...list, ticker]));
  const set = (key: keyof Shocks) => (value: number) => { setPresetName(""); setShocks((previous) => ({ ...previous, [key]: value })); };

  if (error) return <Notice tone="warn">{error}</Notice>;
  if (!data) return <Skeleton height={480} />;
  const snapshot = data.snapshot;
  const topReturn = best(snapshot, (row) => row.return);
  const calmest = best(snapshot, (row) => row.volatility, false);
  const topMargin = best(snapshot, (row) => row.net_margin);
  const colors = Object.fromEntries(data.universe.map((company, index) => [company.ticker, SERIES[index % SERIES.length]]));

  return (
    <>
      <PageHead kicker="Analyst watchlist" title="Your companies, side by side">
        Pick companies to follow, compare how they've done, and see how a downturn could hit their profits and balance sheets.
      </PageHead>
      <div className="toolbar">
        <div className="row">
          <input className="input" style={{ width: 240 }} placeholder="Find by name, ticker or sector" value={search} onChange={(event) => setSearch(event.target.value)} aria-label="Find companies" />
          <div className="chips">
            {data.sectors.map((sector) => (
              <button key={sector} type="button" className="chip" aria-pressed={sectors.includes(sector)}
                onClick={() => setSectors((list) => (list.includes(sector) ? list.filter((item) => item !== sector) : [...list, sector]))}>{sector}</button>
            ))}
          </div>
        </div>
        <ViewPicker views={data.views} value={viewKey} onChange={setViewKey} />
      </div>

      <div className="grid cols-3">
        {data.universe.filter((company) => data.matches.includes(company.ticker)).map((company) => {
          const on = selected.includes(company.ticker);
          return (
            <button key={company.ticker} type="button" onClick={() => toggle(company.ticker)} aria-pressed={on}
              style={{ textAlign: "left", cursor: "pointer", background: on ? "var(--accent-soft)" : "transparent", border: `1px solid ${on ? "var(--accent)" : "var(--rule)"}`, padding: 14 }}>
              <div className="row between"><strong style={{ fontFamily: "var(--serif)", fontSize: 19 }}>{company.name}</strong><span className="tag">{on ? "Following" : "Follow"}</span></div>
              <div className="small muted">{company.ticker} · {company.sector} · also known as {company.aliases}</div>
            </button>
          );
        })}
        {data.matches.length === 0 && <p className="muted">No company matches that search.</p>}
      </div>

      {!snapshot.length ? <div className="section"><Notice>Follow at least one company to build the comparison.</Notice></div> : (
        <>
          <div className="grid cols-3 section">
            <Figure label="Best return" value={`${topReturn?.name}`} note={percent(topReturn?.return, 1, true)} />
            <Figure label="Steadiest price" value={`${calmest?.name}`} note={`${percent(calmest?.volatility)} yearly swing`} />
            <Figure label="Highest profit margin" value={`${topMargin?.name}`} note={percent(topMargin?.net_margin)} />
          </div>

          <div className="grid cols-main section">
            <Block title="Performance, starting from 100">
              <div style={{ height: 260 }}>
                <ResponsiveContainer>
                  <LineChart data={data.indexed} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                    <CartesianGrid vertical={false} />
                    <XAxis dataKey="date" tickFormatter={shortDay} tickLine={false} axisLine={false} />
                    <YAxis width={40} tickLine={false} axisLine={false} domain={["auto", "auto"]} />
                    <Tooltip labelFormatter={(label) => day(String(label))} formatter={(value) => number(Number(value), 1)} />
                    <Legend iconType="plainline" />
                    {selected.map((ticker) => <Line key={ticker} dataKey={ticker} stroke={colors[ticker]} strokeWidth={2.2} dot />)}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Block>
            <Block title="Key numbers">
              <table className="table">
                <thead><tr><th>Company</th><th className="right">Return</th><th className="right">Margin</th><th className="right">Debt / equity</th></tr></thead>
                <tbody>
                  {snapshot.map((row) => (
                    <tr key={row.ticker}>
                      <td><span className="row" style={{ gap: 6 }}><span style={{ width: 10, height: 10, background: colors[row.ticker], display: "inline-block" }} />{row.name}</span></td>
                      <td className={`right ${row.return >= 0 ? "pos" : "neg"}`}>{percent(row.return, 1, true)}</td>
                      <td className="right">{percent(row.net_margin)}</td>
                      <td className="right">{ratio(row.debt_to_equity)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="small muted">Revenue and profit in {snapshot[0].unit}.</p>
            </Block>
          </div>

          <Block title="What if business gets worse?" className="section" sub="Shock revenue, margins and the balance sheet. No probability is attached — this is sensitivity, not a forecast."
            action={<Tabs label="Starting point" value={presetName} onChange={(name) => { setPresetName(name); setShocks(fromPreset(data.presets[name])); }}
              options={Object.keys(data.presets).map((name) => ({ key: name, label: name }))} />}>
            <div className="grid cols-3" style={{ gap: 18 }}>
              <Slider label="Revenue" value={shocks.revenue} min={-0.5} max={0.5} step={0.01} display={percent(shocks.revenue, 0, true)} onChange={set("revenue")} />
              <Slider label="Profit margin" value={shocks.margin_bps} min={-2000} max={2000} step={25} display={`${shocks.margin_bps >= 0 ? "+" : "−"}${number(Math.abs(shocks.margin_bps) / 100, 2)} pts`} onChange={set("margin_bps")} />
              <Slider label="Short-term assets" value={shocks.assets} min={-0.5} max={0.5} step={0.01} display={percent(shocks.assets, 0, true)} onChange={set("assets")} />
              <Slider label="Short-term debts" value={shocks.liabilities} min={-0.5} max={0.5} step={0.01} display={percent(shocks.liabilities, 0, true)} onChange={set("liabilities")} />
              <Slider label="Total debt" value={shocks.debt} min={-0.5} max={1} step={0.01} display={percent(shocks.debt, 0, true)} onChange={set("debt")} />
              <Slider label="Shareholders' equity" value={shocks.equity} min={-0.5} max={0.5} step={0.01} display={percent(shocks.equity, 0, true)} onChange={set("equity")} />
            </div>
            {stress.error ? <Notice tone="warn">{stress.error}</Notice> : stress.data && (
              <div className="grid cols-2 section" style={{ marginTop: 24 }}>
                <div style={{ height: 240 }}>
                  <ResponsiveContainer>
                    <BarChart data={stress.data.rows} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                      <CartesianGrid vertical={false} />
                      <XAxis dataKey="name" tickLine={false} axisLine={false} />
                      <YAxis width={44} tickLine={false} axisLine={false} />
                      <Tooltip formatter={(value) => `${number(Number(value), 1)} ${stress.data!.unit}`} cursor={{ fill: "var(--surface-2)" }} />
                      <Legend iconType="square" />
                      <Bar dataKey="net_income" name="Profit today" fill="var(--faint)" />
                      <Bar dataKey="stressed_net_income" name="Profit under stress" fill="var(--accent)" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <table className="table">
                  <thead><tr><th>Company</th><th className="right">Profit change</th><th className="right">Bills cover</th><th className="right">Debt / equity</th></tr></thead>
                  <tbody>
                    {stress.data.rows.map((row) => (
                      <tr key={row.ticker}>
                        <td>{row.name}</td>
                        <td className={`right ${row.change >= 0 ? "pos" : "neg"}`}>{row.change >= 0 ? "+" : "−"}{number(Math.abs(row.change), 1)}</td>
                        <td className="right">{ratio(row.current_ratio)} → <strong>{ratio(row.stressed_current_ratio)}</strong></td>
                        <td className="right">{ratio(row.debt_to_equity)} → <strong>{ratio(row.stressed_debt_to_equity)}</strong></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Block>

          <Block title="Where these numbers come from" className="section">
            <table className="table">
              <thead><tr><th>Company</th><th>Prices</th><th>Accounts</th></tr></thead>
              <tbody>
                {snapshot.map((row) => (
                  <tr key={row.ticker}>
                    <td>{row.name}</td>
                    <td className="small">{row.price_source}<div className="muted">available {day(row.price_available_at)}</div></td>
                    <td className="small">{row.filing_source}<div className="muted">available {day(row.filing_available_at)}</div></td>
                  </tr>
                ))}
              </tbody>
            </table>
            {data.identity && <p className="small muted">Snapshot fingerprint: <span className="hash">{data.identity}</span></p>}
          </Block>
        </>
      )}
    </>
  );
}
