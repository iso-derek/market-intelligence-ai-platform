"""Native Streamlit presentation for the bounded D2 analytical fixture."""
from pathlib import Path

import pandas as pd
import streamlit as st

from market_data import (
    FixtureProvider,
    fundamental_ratios,
    fundamentals_as_of,
    macro_as_of,
    price_performance,
    prices_as_of,
)


FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "data" / "fixtures"
CUTOFFS = {
    "31 January 2026 — before revisions": "2026-01-31T23:59:59Z",
    "1 March 2026 — revised history": "2026-03-01T23:59:59Z",
}


@st.cache_data
def load_market_bundle(root: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load normalized provider data once per fixture revision."""
    provider = FixtureProvider(Path(root))
    return provider.prices(), provider.macro(), provider.fundamentals()


def render_market_dashboard() -> None:
    """Render a point-in-time market, macro, and company research workspace."""
    prices, macro, fundamentals = load_market_bundle(str(FIXTURE_ROOT))
    with st.sidebar:
        st.header("Point-in-time controls")
        cutoff_label = st.selectbox("Historical view", list(CUTOFFS), index=1, key="market_cutoff")
        instrument = st.selectbox(
            "Focus company",
            prices[["instrument", "instrument_name"]]
            .drop_duplicates()
            .apply(lambda row: f"{row.instrument} — {row.instrument_name}", axis=1)
            .tolist(),
            key="market_instrument",
        ).split(" — ", 1)[0]
        st.info("All observations are deterministic educational fixtures, not live prices or investment advice.")

    cutoff = CUTOFFS[cutoff_label]
    available_prices = prices_as_of(prices, cutoff)
    performance = price_performance(prices, cutoff)
    available_macro = macro_as_of(macro, cutoff)
    available_fundamentals = fundamentals_as_of(fundamentals, cutoff)
    peers = fundamental_ratios(fundamentals, cutoff)

    st.subheader("Market, macro & fundamentals lab")
    st.caption(f"Historical cutoff: {pd.Timestamp(cutoff).isoformat()} · only records available by this time are used")

    selected = performance.set_index("instrument").loc[instrument]
    metric_columns = st.columns(4)
    metric_columns[0].metric(
        "Adjusted close",
        f"{selected.latest_adjusted_close:,.2f} {selected.currency}",
        border=True,
    )
    metric_columns[1].metric("Cumulative return", f"{selected.cumulative_return:.2%}", border=True)
    metric_columns[2].metric("Annualized volatility", f"{selected.annualized_volatility:.2%}", border=True)
    metric_columns[3].metric("Trading calendar", selected.calendar, border=True)

    market_tab, macro_tab, company_tab, method_tab = st.tabs(
        ["Market prices", "Macro vintages", "Company peers", "Methodology"]
    )

    with market_tab:
        selected_prices = available_prices.loc[available_prices.instrument.eq(instrument)].copy()
        st.line_chart(
            selected_prices,
            x="date",
            y=["raw_close", "adjusted_close"],
            x_label="Market close (UTC)",
            y_label=f"Close ({selected.currency})",
            alt=f"Raw and adjusted closes for {instrument}; the adjusted series removes the split discontinuity",
        )
        st.caption("Adjusted closes are used for performance. Raw closes remain visible so corporate-action effects are auditable.")
        display_prices = selected_prices[
            ["date", "raw_close", "adjusted_close", "currency", "calendar", "available_at", "source_version"]
        ]
        st.dataframe(
            display_prices,
            hide_index=True,
            column_config={
                "raw_close": st.column_config.NumberColumn("Raw close", format="%.2f"),
                "adjusted_close": st.column_config.NumberColumn("Adjusted close", format="%.2f"),
            },
            alt=f"Point-in-time raw and adjusted price records for {instrument}",
        )
        st.subheader("Bounded universe comparison")
        st.dataframe(
            performance,
            hide_index=True,
            column_config={
                "cumulative_return": st.column_config.NumberColumn("Cumulative return", format="percent"),
                "annualized_volatility": st.column_config.NumberColumn("Annualized volatility", format="percent"),
            },
            alt="Return and volatility comparison for the three-company educational universe",
        )

    with macro_tab:
        latest_macro = (
            available_macro.sort_values("observation_date")
            .drop_duplicates("series_id", keep="last")
            .reset_index(drop=True)
        )
        cards = st.columns(min(4, len(latest_macro)))
        for card, row in zip(cards, latest_macro.itertuples(index=False)):
            card.metric(row.series_name, f"{row.value:g} {row.unit}", border=True)
        st.dataframe(
            available_macro[
                ["series_id", "series_name", "observation_date", "value", "unit", "release_at", "vintage_at", "available_at", "source"]
            ],
            hide_index=True,
            alt="Macro observations and the latest vintage eligible at the selected historical cutoff",
        )
        st.caption("Changing the cutoff demonstrates the CPI revision: 2.9 before 15 February and 3.0 afterward.")

    with company_tab:
        peer_display = peers.rename(
            columns={
                "company": "Ticker",
                "company_name": "Company",
                "sector": "Sector",
                "fiscal_period_end": "Fiscal period end",
                "report_version": "Report version",
                "currency": "Currency",
                "unit": "Unit",
                "available_at": "Available at",
                "source": "Source",
                "revenue": "Revenue",
                "net_income": "Net income",
                "net_margin": "Net margin",
                "current_ratio": "Current ratio",
                "debt_to_equity": "Debt / equity",
            }
        )
        st.dataframe(
            peer_display,
            hide_index=True,
            column_config={
                "Revenue": st.column_config.NumberColumn(format="%,.0f"),
                "Net income": st.column_config.NumberColumn(format="%,.0f"),
                "Net margin": st.column_config.NumberColumn(format="percent"),
                "Current ratio": st.column_config.NumberColumn(format="%.2f"),
                "Debt / equity": st.column_config.NumberColumn(format="%.2f"),
            },
            alt="Point-in-time profitability, liquidity, and leverage ratios for the company peer set",
        )
        st.caption("Revenue and net income use the displayed currency and unit; ratios are dimensionless.")
        focus_facts = available_fundamentals.loc[available_fundamentals.company.eq(instrument)]
        st.subheader(f"{instrument} report evidence")
        focus_display = focus_facts[
            ["fiscal_period_end", "filed_at", "available_at", "report_version", "metric", "value", "currency", "unit", "source"]
        ].rename(
            columns={
                "fiscal_period_end": "Fiscal period end",
                "filed_at": "Filed at",
                "available_at": "Available at",
                "report_version": "Report version",
                "metric": "Metric",
                "value": "Value",
                "currency": "Currency",
                "unit": "Unit",
                "source": "Source",
            }
        )
        st.dataframe(
            focus_display,
            hide_index=True,
            alt=f"Selected report version and underlying accounting facts for {instrument}",
        )
        st.caption("A report version is selected as a whole. Facts from an earlier filing are never mixed with a later restatement.")

    with method_tab:
        st.markdown(
            """
            **Price return**

            `r_t = adjusted_close_t / adjusted_close_(t-1) - 1`

            **Annualized volatility**

            `sample standard deviation(daily returns) × √252`

            **Company ratios**

            `net margin = net income / revenue`

            `current ratio = current assets / current liabilities`

            `debt to equity = total debt / shareholders' equity`
            """
        )
        st.info(
            "Point-in-time rule: a record is eligible only when available_at is no later than the selected cutoff. "
            "Macro data then selects the latest eligible vintage; company data selects one complete eligible report version."
        )
        st.write(
            "Provider boundary: the dashboard consumes normalized price, macro, and fundamental tables through a small protocol. "
            "The bundled provider reads local fixtures and performs no network access."
        )
