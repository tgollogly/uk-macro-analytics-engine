"""
Portfolio dashboard: ONS macro series with KPIs, Plotly charts, and exports.

Run locally (free):
  streamlit run streamlit_app.py

**Refresh data** re-downloads ONS CSVs (then Parquet cache updates). Host the app free on
Streamlit Community Cloud; use `static-site/` on Vercel for a fast landing page (see docs/VERCEL.md).
"""

from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.analytics import cpih_rolling_and_yoy, fiscal_monthly_totals
from src.config import get_settings
from src.data_fetcher import fetch_and_register
from src.db_engine import connect_duckdb, setup_database

PAGE_TITLE = "UK Macro Analytics — Thomas Gollogly"


def _plot_line(df: pd.DataFrame, x: str, y: str, title: str, y_title: str) -> go.Figure:
    d = df.copy()
    d[x] = pd.to_datetime(d[x])
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=d[x],
            y=d[y],
            mode="lines",
            line=dict(color="#3b82f6", width=2),
            fill="tozeroy",
            fillcolor="rgba(59, 130, 246, 0.12)",
            name=y_title,
        )
    )
    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        paper_bgcolor="#0f172a",
        plot_bgcolor="#1e293b",
        font=dict(color="#f8fafc", family="system-ui, sans-serif"),
        margin=dict(l=48, r=24, t=48, b=48),
        height=420,
        xaxis=dict(gridcolor="#334155", showgrid=True),
        yaxis=dict(gridcolor="#334155", showgrid=True, title=y_title),
        hovermode="x unified",
    )
    return fig


@st.cache_data(ttl=600, show_spinner="Loading ONS data and analytics…")
def _load_dashboard(refresh_id: int) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    force_refresh = refresh_id > 0
    settings = get_settings()
    con = connect_duckdb(settings)
    try:
        fetch_and_register(
            "ons_cpih_monthly",
            con,
            "ons_cpih_monthly",
            settings,
            force_refresh=force_refresh,
        )
        fetch_and_register(
            "ons_psnb_monthly",
            con,
            "ons_psnb_monthly",
            settings,
            force_refresh=force_refresh,
        )
        setup_database(con, with_indexes=True)
        cpih_df = cpih_rolling_and_yoy(con).df()
        psnb_df = fiscal_monthly_totals(con).df()
        fetched = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
        return cpih_df, psnb_df, fetched
    finally:
        con.close()


def main() -> None:
    st.set_page_config(
        page_title=PAGE_TITLE,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    if "refresh_id" not in st.session_state:
        st.session_state.refresh_id = 0

    st.title("UK macro analytics dashboard")
    st.caption("Portfolio · Thomas Gollogly · ONS open data · DuckDB · Streamlit")

    with st.sidebar:
        st.header("Data")
        st.markdown(
            "**Refresh data** pulls the latest CSV from the ONS URLs in `src/config.py` and "
            "updates the Parquet cache. This is the closest to ‘live’ open data without a paid API."
        )
        if st.button("Refresh data from ONS", type="primary"):
            st.session_state.refresh_id += 1
            st.rerun()
        st.divider()
        st.markdown("**Quick links**")
        st.markdown(
            "- [GitHub repository](https://github.com/tgollogly/uk-macro-analytics-engine)\n"
            "- [Portfolio](https://tgollogly.dev)"
        )

    cpih_df, psnb_df, fetched_at = _load_dashboard(st.session_state.refresh_id)

    st.caption(f"Snapshot **{fetched_at}** (UTC)")

    yoy_valid = cpih_df.dropna(subset=["yoy_pct"])
    k1, k2, k3, k4 = st.columns(4)

    if not yoy_valid.empty:
        last_y = yoy_valid.iloc[-1]
        prev_y = yoy_valid.iloc[-2] if len(yoy_valid) > 1 else last_y
        delta = float(last_y["yoy_pct"]) - float(prev_y["yoy_pct"])
        k1.metric(
            "CPIH YoY %",
            f"{float(last_y['yoy_pct']):.2f}%",
            f"{delta:+.2f} pp vs prior month" if len(yoy_valid) > 1 else None,
            help="Year-on-year % change, CPIH all items (ONS L522).",
        )
        # 12-month change in YoY (momentum)
        if len(yoy_valid) >= 13:
            y_12 = yoy_valid.iloc[-13]
            mom = float(last_y["yoy_pct"]) - float(y_12["yoy_pct"])
            k3.metric(
                "YoY momentum (12m)",
                f"{mom:+.2f} pp",
                "vs same month last year",
                help="Change in YoY% over the last year — broad ‘acceleration’ signal.",
            )
        else:
            k3.metric("YoY momentum", "—")
    else:
        k1.metric("CPIH YoY %", "—")
        k3.metric("YoY momentum", "—")

    if not psnb_df.empty:
        last_p = psnb_df.iloc[-1]
        prev_p = psnb_df.iloc[-2] if len(psnb_df) > 1 else last_p
        dpm = float(last_p["total_net_borrowing_gbp_m"]) - float(
            prev_p["total_net_borrowing_gbp_m"]
        )
        k2.metric(
            "PSNB (£m)",
            f"{float(last_p['total_net_borrowing_gbp_m']):,.0f}",
            f"{dpm:+,.0f} vs prior month" if len(psnb_df) > 1 else None,
            help="Public sector net borrowing ex. public sector banks (ONS DZLS).",
        )
    else:
        k2.metric("PSNB (£m)", "—")

    k4.metric(
        "Pipeline",
        "DuckDB + pytest + CI",
        "see GitHub",
        help="Automated validation, tests, and lint in GitHub Actions.",
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Overview", "CPIH inflation", "Public finances", "Insights", "About / deploy"]
    )

    with tab1:
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            if not yoy_valid.empty:
                ch = yoy_valid.tail(84).copy()
                fig = _plot_line(
                    ch,
                    "obs_date",
                    "yoy_pct",
                    "CPIH year-on-year %",
                    "%",
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No CPIH YoY series.")
        with c2:
            if not psnb_df.empty:
                cp = psnb_df.tail(84).copy()
                fig2 = _plot_line(
                    cp,
                    "obs_date",
                    "total_net_borrowing_gbp_m",
                    "PSNB monthly (£ million)",
                    "£m",
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No PSNB series.")

    with tab2:
        if yoy_valid.empty:
            st.warning("No YoY values.")
        else:
            horizon = st.slider("Months shown", 24, 240, 96, 12, key="cpih_horizon")
            sub = yoy_valid.tail(horizon).copy()
            fig = _plot_line(sub, "obs_date", "yoy_pct", "CPIH YoY % — selected window", "%")
            st.plotly_chart(fig, use_container_width=True)
            show = sub.tail(24)[
                ["obs_date", "index_level", "cpih_3m_avg", "yoy_pct"]
            ].copy()
            show["obs_date"] = pd.to_datetime(show["obs_date"]).dt.date.astype(str)
            st.dataframe(
                show,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "yoy_pct": st.column_config.NumberColumn("YoY %", format="%.2f"),
                    "index_level": st.column_config.NumberColumn("Index", format="%.1f"),
                    "cpih_3m_avg": st.column_config.NumberColumn("3m avg", format="%.2f"),
                },
            )
            buf = BytesIO()
            sub.to_csv(buf, index=False)
            st.download_button(
                "Download CPIH YoY (CSV)",
                buf.getvalue(),
                file_name="cpih_yoy_export.csv",
                mime="text/csv",
            )

    with tab3:
        if psnb_df.empty:
            st.warning("No PSNB rows.")
        else:
            horizon = st.slider("Months shown", 24, 240, 96, 12, key="psnb_horizon")
            subp = psnb_df.tail(horizon).copy()
            fig = _plot_line(
                subp,
                "obs_date",
                "total_net_borrowing_gbp_m",
                "PSNB — selected window",
                "£m",
            )
            st.plotly_chart(fig, use_container_width=True)
            subp_show = subp.tail(24).copy()
            subp_show["obs_date"] = pd.to_datetime(subp_show["obs_date"]).dt.date.astype(str)
            st.dataframe(subp_show, use_container_width=True, hide_index=True)
            buf2 = BytesIO()
            subp.to_csv(buf2, index=False)
            st.download_button(
                "Download PSNB (CSV)",
                buf2.getvalue(),
                file_name="psnb_monthly_export.csv",
                mime="text/csv",
            )

    with tab4:
        st.subheader("Plain-language read (from latest pull)")
        if yoy_valid.empty or psnb_df.empty:
            st.info("Run Refresh if series are empty.")
        else:
            ly = yoy_valid.iloc[-1]
            lp = psnb_df.iloc[-1]
            st.markdown(
                f"- **Inflation (CPIH YoY)** was **{float(ly['yoy_pct']):.2f}%** in "
                f"**{str(ly['obs_date'])[:10]}**.\n"
                f"- **Public borrowing (PSNB)** was **£{float(lp['total_net_borrowing_gbp_m']):,.0f}m** "
                f"in **{str(lp['obs_date'])[:10]}**.\n"
                "- These are **official statistics** from ONS CSVs at download time; "
                "ONS can **revise** past months — treat as operational monitoring, not trading advice."
            )
            if len(yoy_valid) >= 13:
                a = float(yoy_valid.iloc[-1]["yoy_pct"])
                b = float(yoy_valid.iloc[-13]["yoy_pct"])
                st.markdown(f"- **YoY inflation** is **{a - b:+.2f} percentage points** vs the same month a year earlier.")

    with tab5:
        st.markdown(
            """
### Portfolio deployment (free)

| Piece | Where |
|-------|--------|
| **Streamlit app** | [Streamlit Community Cloud](https://streamlit.io/cloud) — connect GitHub, entry `streamlit_app.py`, Python 3.11 |
| **Landing page (static)** | Folder `static-site/` → deploy on **[Vercel](https://vercel.com)** with root = `static-site` (see `docs/VERCEL.md`) |

Vercel **cannot** run Streamlit’s Python server on typical hobby static/serverless — use Cloud for the dashboard, Vercel for the brochure page.

### Tech you can name in interviews

Python · DuckDB · pandas · Plotly · Streamlit · requests · pytest · Ruff · GitHub Actions · Parquet · ONS data (OGL).
            """
        )

    st.divider()
    st.caption(
        "© Thomas Gollogly — dashboard & pipeline code (MIT). "
        "Statistics © Crown copyright — Office for National Statistics — "
        "Open Government Licence v3.0."
    )


if __name__ == "__main__":
    main()
