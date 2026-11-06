"""
Portfolio dashboard: ONS macro series with KPIs, Plotly charts, and exports.

Run locally (free):
  streamlit run streamlit_app.py

**Refresh data** re-downloads ONS CSVs (then Parquet cache updates). Host the app free on
Streamlit Community Cloud; use `static-site/` on Vercel for a fast landing page (see `docs/VERCEL.md`).
"""

from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.analytics import cpih_rolling_and_yoy, fiscal_monthly_totals
from src.config import Settings, get_settings
from src.data_fetcher import DataFetchError, fetch_and_register
from src.db_engine import connect_duckdb, setup_database

PAGE_TITLE = "UK Macro Analytics"
# Accessible palette: high contrast on dark backgrounds (WCAG-friendly pairing)
CPIH_LINE = "#38bdf8"
CPIH_FILL = "rgba(56, 189, 248, 0.14)"
PSNB_LINE = "#a78bfa"
PSNB_FILL = "rgba(167, 139, 250, 0.12)"
PLOT_BG = "#1e293b"
PAPER_BG = "#0f172a"
GRID_COLOR = "#334155"


def _plot_line(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    y_title: str,
    *,
    line_color: str,
    fill_color: str,
) -> go.Figure:
    d = df.copy()
    d[x] = pd.to_datetime(d[x])
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=d[x],
            y=d[y],
            mode="lines",
            line=dict(color=line_color, width=2.5),
            fill="tozeroy",
            fillcolor=fill_color,
            name=y_title,
            hovertemplate=(
                "<b>%{fullData.name}</b><br>"
                "%{x|%Y-%m-%d}<br>"
                "%{y:,.2f}<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        title=dict(text=title, font=dict(size=17), x=0, xanchor="left"),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(color="#f8fafc", family="system-ui, Segoe UI, Roboto, sans-serif", size=13),
        margin=dict(l=56, r=20, t=52, b=48),
        height=420,
        xaxis=dict(
            gridcolor=GRID_COLOR,
            showgrid=True,
            title="Date",
            rangeselector=dict(
                buttons=[
                    dict(count=24, label="2y", step="month", stepmode="backward"),
                    dict(count=60, label="5y", step="month", stepmode="backward"),
                    dict(count=120, label="10y", step="month", stepmode="backward"),
                    dict(label="All", step="all"),
                ],
                bgcolor="#1e293b",
                bordercolor="#475569",
                font=dict(color="#e2e8f0"),
            ),
            rangeslider=dict(visible=False),
            type="date",
        ),
        yaxis=dict(gridcolor=GRID_COLOR, showgrid=True, title=dict(text=y_title)),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
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


def _format_dataset_urls(settings: Settings) -> str:
    """Markdown lines for sidebar / provenance (sources from config — no invented URLs)."""
    lines: list[str] = []
    for key in ("ons_cpih_monthly", "ons_psnb_monthly"):
        spec = settings.datasets[key]
        lines.append(f"- **{key}** — {spec.description.strip()}")
        lines.append(f"  - Config URL: `{spec.url}`")
    return "\n".join(lines)


def _validation_summary(cpih_df: pd.DataFrame, psnb_df: pd.DataFrame) -> str:
    """Short, factual counts from the loaded frames (for transparency)."""
    parts: list[str] = []
    if not cpih_df.empty:
        dmin = pd.to_datetime(cpih_df["obs_date"]).min()
        dmax = pd.to_datetime(cpih_df["obs_date"]).max()
        n = len(cpih_df)
        yoy_null = int(cpih_df["yoy_pct"].isna().sum())
        idx_null = int(cpih_df["index_level"].isna().sum())
        parts.append(
            f"- **CPIH (after SQL prep):** {n} monthly rows from **{dmin.date()}** to **{dmax.date()}**."
        )
        parts.append(
            f"- **YoY % missing:** {yoy_null} rows — expected where fewer than 12 prior months exist "
            "or the lag index is zero (see `src/analytics.py`)."
        )
        if idx_null:
            parts.append(f"- **Index level missing:** {idx_null} rows (dropped from YoY path).")
    else:
        parts.append("- **CPIH:** no rows returned.")
    if not psnb_df.empty:
        dmin = pd.to_datetime(psnb_df["obs_date"]).min()
        dmax = pd.to_datetime(psnb_df["obs_date"]).max()
        n = len(psnb_df)
        multi = psnb_df[psnb_df["row_count"] > 1]
        parts.append(
            f"- **PSNB (aggregated monthly):** {n} months from **{dmin.date()}** to **{dmax.date()}**."
        )
        if not multi.empty:
            parts.append(
                f"- **PSNB row_count greater than 1:** {len(multi)} month(s) — source CSV had multiple "
                "rows per month; values are **summed** in SQL (see `fiscal_monthly_totals`)."
            )
    else:
        parts.append("- **PSNB:** no rows returned.")
    return "\n".join(parts)


def main() -> None:
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(
        '<a href="#main-dashboard" class="skip-link" style="position:absolute;left:-9999px;'
        'z-index:999;padding:0.5rem 1rem;background:#1d4ed8;color:#fff;'
        'text-decoration:none;border-radius:4px;">Skip to dashboard</a>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "<style>.skip-link:focus{left:0.5rem;top:0.5rem;position:fixed;}</style>",
        unsafe_allow_html=True,
    )

    if "refresh_id" not in st.session_state:
        st.session_state.refresh_id = 0

    st.markdown('<div id="main-dashboard"></div>', unsafe_allow_html=True)
    st.title("UK macro analytics dashboard")
    st.caption(
        "Analyst-style portfolio piece: **provenance**, **validation**, **trends**, and "
        "**limitations** — Office for National Statistics open CSVs · DuckDB · Parquet cache · "
        "Streamlit · Plotly · automated tests in CI"
    )

    with st.sidebar:
        st.header("Data sources")
        st.markdown(
            "**Refresh** re-downloads the configured CSVs, checks expected columns, writes **Parquet**, "
            "and reloads **DuckDB**. ONS publishes on its own schedule — this is **not** a live market feed."
        )
        if st.button("Refresh data from ONS", type="primary", use_container_width=True):
            st.session_state.refresh_id += 1
            st.rerun()
        st.divider()
        st.markdown("**Links**")
        st.markdown(
            "- [Repository](https://github.com/tgollogly/uk-macro-analytics-engine)\n"
            "- [ONS — CPIH](https://www.ons.gov.uk/economy/inflationandpriceindices)\n"
            "- [ONS — public sector finance](https://www.ons.gov.uk/economy/governmentpublicsectorandtaxes/publicsectorfinance)"
        )

    try:
        cpih_df, psnb_df, fetched_at = _load_dashboard(st.session_state.refresh_id)
    except DataFetchError as exc:
        st.error(
            "**Could not download data** — check your network connection, firewall, or whether "
            "the ONS generator URL in `src/config.py` still matches the live site."
        )
        st.caption(str(exc))
        if st.button("Retry download"):
            st.session_state.refresh_id += 1
            st.rerun()
        st.stop()
    except Exception as exc:  # noqa: BLE001 — surface unexpected failures in the UI
        st.error("**Unexpected error while loading data.** See details below for debugging.")
        st.exception(exc)
        st.stop()

    st.success(f"Session snapshot **{fetched_at}** (UTC) — data read successfully.", icon="✅")

    settings = get_settings()
    with st.expander("**Provenance & definitions** (what the numbers are)", expanded=False):
        st.markdown(
            "**Download time** above is when this app finished loading; ONS may publish **revisions** "
            "later — always confirm headline figures on [ons.gov.uk](https://www.ons.gov.uk/).\n\n"
            "**Licence:** statistics are © Crown copyright, used under the "
            "[Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/) "
            "(see `NOTICE.md`).\n\n"
            "**Series (from `src/config.py`):**\n"
            "- **CPIH YoY %** — year-on-year % change in the **CPIH all-items index** "
            "(ONS time-series **L522** via the generator URL below). 3-month **rolling average** of the "
            "index is computed in SQL before YoY.\n"
            "- **PSNB** — **public sector net borrowing** excluding public sector banks, **monthly**, "
            "£ **million** (ONS **DZLS** / PUSF via the generator URL below).\n\n"
            f"{_format_dataset_urls(settings)}"
        )
    with st.expander("**Data quality & validation** (this run — from the loaded tables)", expanded=False):
        st.markdown(_validation_summary(cpih_df, psnb_df))
        st.markdown(
            "\n**Pipeline checks (automated):** schema + column aliases in `src/data_fetcher.py`, "
            "pytest in `tests/` — see **Quality** metric and GitHub Actions."
        )

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
            help="YoY % = 100 × (indexₜ − indexₜ₋₁₂) / indexₜ₋₁₂ on monthly CPIH (ONS L522).",
        )
        if len(yoy_valid) >= 13:
            y_12 = yoy_valid.iloc[-13]
            mom = float(last_y["yoy_pct"]) - float(y_12["yoy_pct"])
            k3.metric(
                "YoY momentum (12m)",
                f"{mom:+.2f} pp",
                "vs same month last year",
                help="Compares latest YoY % to the same calendar month one year ago — descriptive only.",
            )
        else:
            k3.metric("YoY momentum (12m)", "—", help="Need more history for 12-month comparison.")
    else:
        k1.metric("CPIH YoY %", "—")
        k3.metric("YoY momentum (12m)", "—")

    if not psnb_df.empty:
        last_p = psnb_df.iloc[-1]
        prev_p = psnb_df.iloc[-2] if len(psnb_df) > 1 else last_p
        dpm = float(last_p["total_net_borrowing_gbp_m"]) - float(prev_p["total_net_borrowing_gbp_m"])
        k2.metric(
            "PSNB (£m)",
            f"{float(last_p['total_net_borrowing_gbp_m']):,.0f}",
            f"{dpm:+,.0f} vs prior month" if len(psnb_df) > 1 else None,
            help="PSNB ex. public sector banks, monthly total £m (ONS DZLS); check footnotes on ONS.",
        )
    else:
        k2.metric("PSNB (£m)", "—")

    k4.metric(
        "Quality",
        "pytest + Ruff + CI",
        "see GitHub Actions",
        help="CI: ruff, compileall, pytest, scripts in src/security_audit.py + pip-audit step.",
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Overview", "CPIH inflation", "Public finances", "Interpretation", "Deploy & stack"]
    )

    with tab1:
        st.markdown(
            "**What this shows:** two ONS **macro** series — **CPIH inflation** (YoY %) and **public "
            "borrowing** (PSNB, £m/month) — after **HTTP fetch**, **column validation**, "
            "**Parquet** cache, and **DuckDB** SQL (rolling window + YoY). "
            "Use the expanders above for **definitions** and **row counts**."
        )
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            if not yoy_valid.empty:
                ch = yoy_valid.tail(84).copy()
                fig = _plot_line(
                    ch,
                    "obs_date",
                    "yoy_pct",
                    "CPIH year-on-year % (latest window)",
                    "%",
                    line_color=CPIH_LINE,
                    fill_color=CPIH_FILL,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No CPIH YoY values in this pull — try **Refresh** or check the fetch logs.")
        with c2:
            if not psnb_df.empty:
                cp = psnb_df.tail(84).copy()
                fig2 = _plot_line(
                    cp,
                    "obs_date",
                    "total_net_borrowing_gbp_m",
                    "PSNB monthly (£ million)",
                    "£m",
                    line_color=PSNB_LINE,
                    fill_color=PSNB_FILL,
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.warning("No PSNB rows — try **Refresh** or verify the ONS URL in config.")

    with tab2:
        if yoy_valid.empty:
            st.warning("No YoY values available.")
        else:
            horizon = st.slider("Months shown", 24, 240, 96, 12, key="cpih_horizon")
            sub = yoy_valid.tail(horizon).copy()
            fig = _plot_line(
                sub,
                "obs_date",
                "yoy_pct",
                "CPIH YoY % — selected window",
                "%",
                line_color=CPIH_LINE,
                fill_color=CPIH_FILL,
            )
            st.plotly_chart(fig, use_container_width=True)
            show = sub.tail(24)[["obs_date", "index_level", "cpih_3m_avg", "yoy_pct"]].copy()
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
                use_container_width=True,
            )

    with tab3:
        if psnb_df.empty:
            st.warning("No PSNB rows in this session.")
        else:
            horizon = st.slider("Months shown", 24, 240, 96, 12, key="psnb_horizon")
            subp = psnb_df.tail(horizon).copy()
            fig = _plot_line(
                subp,
                "obs_date",
                "total_net_borrowing_gbp_m",
                "PSNB — selected window",
                "£m",
                line_color=PSNB_LINE,
                fill_color=PSNB_FILL,
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
                use_container_width=True,
            )

    with tab4:
        st.subheader("Business-style read (from the latest successful pull — not advice)")
        if yoy_valid.empty or psnb_df.empty:
            st.info("Need both series for a paired read — use **Refresh** or check validation expander.")
        else:
            ly = yoy_valid.iloc[-1]
            lp = psnb_df.iloc[-1]
            st.markdown(
                f"- **Inflation (CPIH YoY)** in this pull: **{float(ly['yoy_pct']):.2f}%** for "
                f"**{str(ly['obs_date'])[:10]}** (ONS L522, as configured).\n"
                f"- **Public borrowing (PSNB)** in this pull: **£{float(lp['total_net_borrowing_gbp_m']):,.0f}m** "
                f"for **{str(lp['obs_date'])[:10]}** (ONS DZLS).\n"
                "- **Interpretation:** read these as **indicators** from one publisher pull, not a "
                "forecast. ONS **revises** series; fiscal data have **fiscal-year** and classification "
                "footnotes on the ONS site.\n"
                "- **Not** investment, tax, or policy advice."
            )
            if len(yoy_valid) >= 13:
                a = float(yoy_valid.iloc[-1]["yoy_pct"])
                b = float(yoy_valid.iloc[-13]["yoy_pct"])
                st.markdown(
                    f"- **YoY inflation vs 12 months earlier (same calendar month):** "
                    f"**{a - b:+.2f} percentage points** — descriptive comparison only."
                )
        st.subheader("Limitations & honesty")
        st.markdown(
            "- **Coverage:** two series only; no forecasting, no seasonal adjustment beyond what ONS embeds in the CSV.\n"
            "- **Missing YoY:** the first ~11 monthly points have **no YoY** by construction (need 12 lags).\n"
            "- **Automation:** `pytest` checks parsing and pipelines; it does not certify ONS correctness.\n"
            "- **Reproducibility:** same `requirements.txt` + **Refresh** pulls current ONS files — results change when ONS updates."
        )

    with tab5:
        st.markdown(
            """
### Deploy (free tiers)

| Piece | Where |
|-------|--------|
| **This dashboard** | [Streamlit Community Cloud](https://streamlit.io/cloud) — connect GitHub, main file `streamlit_app.py`, Python 3.11+, `requirements.txt` |
| **Landing page** | Deploy folder `static-site/` on **[Vercel](https://vercel.com)** (root directory = `static-site`). See **`docs/VERCEL.md`**. |

Vercel’s default hobby offering serves static assets; it does **not** host Streamlit’s long-lived Python process — use Streamlit Cloud (or local `streamlit run`) for the interactive app.

### Stack (accurate for a CV bullet)

Python · pandas · DuckDB · Plotly · Streamlit · requests · Parquet · pytest · Ruff · GitHub Actions · ONS open data (OGL).
            """
        )

    st.divider()
    st.caption(
        "Software in this repository: MIT License — see `LICENSE`. "
        "Statistics: © Crown copyright, Office for National Statistics — "
        "[Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/)."
    )


if __name__ == "__main__":
    main()
