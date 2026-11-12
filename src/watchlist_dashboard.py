"""Native Streamlit analyst watchlist presentation."""
from pathlib import Path

import pandas as pd
import streamlit as st

from entities import load_entity_registry
from market_dashboard import CUTOFFS, FIXTURE_ROOT, load_market_bundle
from scenario_analysis import SCENARIO_PRESETS, ScenarioAssumptions, scenario_hash, stress_watchlist
from watchlist import (
    company_universe,
    normalized_performance,
    search_companies,
    snapshot_hash,
    watchlist_snapshot,
)


@st.cache_data
def load_watchlist_registry(path: str) -> pd.DataFrame:
    return load_entity_registry(Path(path))


def render_watchlist_dashboard() -> None:
    """Render search, persistent selection, comparison, and indexed performance."""
    prices, _, fundamentals = load_market_bundle(str(FIXTURE_ROOT))
    registry = load_watchlist_registry(str(FIXTURE_ROOT / "entity_registry.csv"))

    st.session_state.setdefault("analyst_watchlist", ["ALP", "BET", "GAM"])
    with st.sidebar:
        st.header("Watchlist controls")
        cutoff_label = st.selectbox("Historical view", list(CUTOFFS), index=1, key="watchlist_cutoff")
        cutoff = CUTOFFS[cutoff_label]
        universe = company_universe(registry, prices, cutoff)
        option_labels = {
            row.ticker: f"{row.ticker} — {row.canonical_name}" for row in universe.itertuples(index=False)
        }
        st.session_state["analyst_watchlist"] = [
            ticker for ticker in st.session_state.analyst_watchlist if ticker in option_labels
        ]
        selected = st.multiselect(
            "Companies",
            list(option_labels),
            format_func=option_labels.get,
            key="analyst_watchlist",
        )
        st.info("Selections persist only in this browser session. All values are fictional educational fixtures.")

    st.subheader("Analyst watchlist")
    st.caption(
        f"Search and compare the bounded company universe as known at {pd.Timestamp(cutoff).isoformat()}. "
        "No live provider or investment recommendation is implied."
    )
    with st.container(horizontal=True, vertical_alignment="bottom"):
        query = st.text_input(
            "Search companies",
            type="search",
            placeholder="Ticker, company, sector, or alias",
            key="watchlist_search",
        )
        sectors = st.pills(
            "Sectors",
            sorted(universe["sector"].unique()),
            selection_mode="multi",
            key="watchlist_sectors",
        )

    matches = search_companies(universe, query, sectors)
    if matches.empty:
        st.info("No bounded-universe company matches every search token and selected sector.")
    else:
        discovery = matches[["ticker", "canonical_name", "sector", "aliases"]].rename(
            columns={
                "ticker": "Ticker",
                "canonical_name": "Company",
                "sector": "Sector",
                "aliases": "Registered aliases",
            }
        )
        st.dataframe(discovery, hide_index=True, alt="Companies matching the watchlist search and sector filters")

    if not selected:
        st.warning("Select at least one company in the sidebar to build the comparison.")
        return

    snapshot = watchlist_snapshot(prices, fundamentals, selected, cutoff)
    identity = snapshot_hash(snapshot)
    returns = snapshot.dropna(subset=["cumulative_return"])
    volatility = snapshot.dropna(subset=["annualized_volatility"])
    margins = snapshot.dropna(subset=["net_margin"])
    cards = st.columns(4)
    cards[0].metric("Companies", len(snapshot), border=True)
    cards[1].metric(
        "Highest return",
        f"{returns.loc[returns.cumulative_return.idxmax(), 'ticker']} · {returns.cumulative_return.max():.2%}",
        border=True,
    )
    cards[2].metric(
        "Lowest volatility",
        f"{volatility.loc[volatility.annualized_volatility.idxmin(), 'ticker']} · {volatility.annualized_volatility.min():.2%}",
        border=True,
    )
    cards[3].metric(
        "Highest net margin",
        f"{margins.loc[margins.net_margin.idxmax(), 'ticker']} · {margins.net_margin.max():.2%}",
        border=True,
    )

    performance_tab, fundamentals_tab, scenario_tab, evidence_tab = st.tabs(
        ["Indexed performance", "Comparable fundamentals", "Stress scenarios", "Snapshot evidence"]
    )
    with performance_tab:
        indexed = normalized_performance(prices, selected, cutoff)
        st.line_chart(
            indexed,
            x="date",
            y="indexed_close",
            color="ticker",
            x_label="Market close (UTC)",
            y_label="Adjusted close, first eligible observation = 100",
            alt="Normalized adjusted-price performance for the selected watchlist companies",
        )
        market_table = snapshot[
            ["ticker", "company_name", "latest_adjusted_close", "currency", "cumulative_return", "annualized_volatility"]
        ]
        st.dataframe(
            market_table,
            hide_index=True,
            column_config={
                "latest_adjusted_close": st.column_config.NumberColumn("Adjusted close", format="%.2f"),
                "cumulative_return": st.column_config.NumberColumn("Cumulative return", format="percent"),
                "annualized_volatility": st.column_config.NumberColumn("Annualized volatility", format="percent"),
            },
            alt="Point-in-time market comparison for the selected watchlist companies",
        )
    with fundamentals_tab:
        fundamental_table = snapshot[
            [
                "ticker",
                "sector",
                "revenue",
                "net_income",
                "net_margin",
                "current_ratio",
                "debt_to_equity",
                "filing_currency",
                "filing_unit",
            ]
        ]
        st.dataframe(
            fundamental_table,
            hide_index=True,
            column_config={
                "revenue": st.column_config.NumberColumn("Revenue", format="%,.0f"),
                "net_income": st.column_config.NumberColumn("Net income", format="%,.0f"),
                "net_margin": st.column_config.NumberColumn("Net margin", format="percent"),
                "current_ratio": st.column_config.NumberColumn("Current ratio", format="%.2f"),
                "debt_to_equity": st.column_config.NumberColumn("Debt / equity", format="%.2f"),
            },
            alt="Point-in-time fundamental comparison for the selected watchlist companies",
        )
        st.caption("Revenue and net income use the displayed filing currency and unit; ratios are dimensionless.")
    with scenario_tab:
        preset_name = st.segmented_control(
            "Starting assumptions",
            list(SCENARIO_PRESETS),
            default="Downside",
            key="scenario_preset",
        )
        preset = SCENARIO_PRESETS[preset_name or "Downside"]
        with st.container(horizontal=True):
            revenue_shock = st.slider(
                "Revenue shock (%)",
                -50,
                50,
                int(preset.revenue_shock * 100),
                key=f"scenario_revenue_{preset_name}",
            )
            margin_shock_bps = st.slider(
                "Net-margin shock (bps)",
                -2_000,
                2_000,
                preset.margin_shock_bps,
                step=25,
                key=f"scenario_margin_{preset_name}",
            )
        with st.container(horizontal=True):
            assets_shock = st.slider(
                "Current-assets shock (%)",
                -50,
                50,
                int(preset.current_assets_shock * 100),
                key=f"scenario_assets_{preset_name}",
            )
            liabilities_shock = st.slider(
                "Current-liabilities shock (%)",
                -50,
                50,
                int(preset.current_liabilities_shock * 100),
                key=f"scenario_liabilities_{preset_name}",
            )
        with st.container(horizontal=True):
            debt_shock = st.slider(
                "Debt shock (%)",
                -50,
                100,
                int(preset.debt_shock * 100),
                key=f"scenario_debt_{preset_name}",
            )
            equity_shock = st.slider(
                "Equity shock (%)",
                -50,
                50,
                int(preset.equity_shock * 100),
                key=f"scenario_equity_{preset_name}",
            )
        assumptions = ScenarioAssumptions(
            revenue_shock=revenue_shock / 100,
            margin_shock_bps=margin_shock_bps,
            current_assets_shock=assets_shock / 100,
            current_liabilities_shock=liabilities_shock / 100,
            debt_shock=debt_shock / 100,
            equity_shock=equity_shock / 100,
        )
        stressed = stress_watchlist(snapshot, assumptions)
        scenario_identity = scenario_hash(stressed, assumptions)
        scenario_cards = st.columns(4)
        unit = f"{stressed.filing_currency.iloc[0]} {stressed.filing_unit.iloc[0]}"
        scenario_cards[0].metric(
            "Stressed net income",
            f"{stressed.stressed_net_income.sum():,.1f} {unit}",
            border=True,
        )
        scenario_cards[1].metric(
            "Net income change",
            f"{stressed.net_income_change.sum():+,.1f} {unit}",
            border=True,
        )
        scenario_cards[2].metric(
            "Lowest current ratio",
            f"{stressed.stressed_current_ratio.min():.2f}",
            border=True,
        )
        scenario_cards[3].metric(
            "Highest debt / equity",
            f"{stressed.stressed_debt_to_equity.max():.2f}",
            border=True,
        )
        st.bar_chart(
            stressed,
            x="ticker",
            y=["net_income", "stressed_net_income"],
            x_label="Company",
            y_label=f"Net income ({unit})",
            stack=False,
            alt="Base and stressed net income for the selected watchlist companies",
        )
        st.dataframe(
            stressed[
                [
                    "ticker",
                    "revenue",
                    "stressed_revenue",
                    "net_margin",
                    "stressed_net_margin",
                    "net_income",
                    "stressed_net_income",
                    "current_ratio",
                    "stressed_current_ratio",
                    "debt_to_equity",
                    "stressed_debt_to_equity",
                ]
            ],
            hide_index=True,
            column_config={
                "net_margin": st.column_config.NumberColumn("Base net margin", format="percent"),
                "stressed_net_margin": st.column_config.NumberColumn("Stressed net margin", format="percent"),
                "current_ratio": st.column_config.NumberColumn("Base current ratio", format="%.2f"),
                "stressed_current_ratio": st.column_config.NumberColumn("Stressed current ratio", format="%.2f"),
                "debt_to_equity": st.column_config.NumberColumn("Base debt / equity", format="%.2f"),
                "stressed_debt_to_equity": st.column_config.NumberColumn("Stressed debt / equity", format="%.2f"),
            },
            alt="Base and stressed profitability liquidity and leverage for each selected company",
        )
        st.code(scenario_identity, language=None)
        st.warning(
            "This is deterministic sensitivity analysis. The shocks have no assigned probability and the output is not a forecast, valuation, or investment recommendation."
        )
    with evidence_tab:
        evidence = snapshot[
            [
                "ticker",
                "latest_date",
                "price_available_at",
                "filing_available_at",
                "price_source",
                "filing_source",
                "cutoff",
            ]
        ]
        st.dataframe(evidence, hide_index=True, alt="Availability cutoff and source evidence for the watchlist snapshot")
        st.code(identity, language=None)
        st.caption("SHA-256 over the sorted displayed snapshot. The identity changes when its values, sources, or cutoff change.")
