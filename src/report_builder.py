"""
Build a static HTML report from pipeline exports (Parquet under data/exports).

Free workflow: run `python -m src.analytics`, then `python -m src.report_builder`.
Open report.html in any browser — no server or paid service required.
"""

from __future__ import annotations

import argparse
import json
import webbrowser
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from src.config import get_settings


def _export_dir() -> Path:
    return get_settings().paths.export_dir


def _escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _load_latest_metrics(base: Path) -> dict[str, float | str | None]:
    out: dict[str, float | str | None] = {}
    cpih_p = base / "cpih_yoy.parquet"
    psnb_p = base / "psnb_monthly.parquet"
    if not cpih_p.is_file() or not psnb_p.is_file():
        return out
    cpih = pd.read_parquet(cpih_p)
    psnb = pd.read_parquet(psnb_p)
    if not cpih.empty and "yoy_pct" in cpih.columns:
        last = cpih.dropna(subset=["yoy_pct"]).iloc[-1]
        out["cpih_yoy_pct"] = round(float(last["yoy_pct"]), 2)
        out["cpih_as_of"] = str(last.get("obs_date", ""))
    if not psnb.empty and "total_net_borrowing_gbp_m" in psnb.columns:
        last_p = psnb.iloc[-1]
        out["psnb_last_gbp_m"] = round(float(last_p["total_net_borrowing_gbp_m"]), 1)
        out["psnb_as_of"] = str(last_p.get("obs_date", ""))
    return out


def _chart_series(base: Path) -> dict[str, list]:
    p = base / "cpih_yoy.parquet"
    if not p.is_file():
        return {"labels": [], "values": []}
    df = pd.read_parquet(p)
    if df.empty or "yoy_pct" not in df.columns:
        return {"labels": [], "values": []}
    tail = df.dropna(subset=["yoy_pct"]).tail(36)
    labels = [str(x)[:10] for x in tail["obs_date"].tolist()]
    values = [float(x) if x == x else None for x in tail["yoy_pct"].tolist()]
    return {"labels": labels, "values": values}


def build_report(
    output: Path | None = None,
    *,
    base: Path | None = None,
) -> Path:
    base = base or _export_dir()
    output = output or (base / "report.html")
    metrics = _load_latest_metrics(base)
    chart_json = json.dumps(_chart_series(base))

    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    yoy = metrics.get("cpih_yoy_pct")
    psnb = metrics.get("psnb_last_gbp_m")

    yoy_display = f"{yoy:.2f}%" if isinstance(yoy, int | float) else "Run the pipeline first"
    psnb_display = f"£{psnb:,.1f}m" if isinstance(psnb, int | float) else "Run the pipeline first"

    # Split template so JSON Chart.js config does not collide with str.format/f-strings.
    head = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>UK Macro — KPI dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.6/dist/chart.umd.min.js"></script>
  <style>
    :root {{
      --bg: #0f172a;
      --card: #1e293b;
      --text: #f8fafc;
      --muted: #94a3b8;
      --accent: #3b82f6;
    }}
    body {{
      font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      margin: 0;
      padding: 1.25rem;
      line-height: 1.45;
    }}
    h1 {{ font-size: 1.35rem; margin: 0 0 0.35rem; }}
    .sub {{ color: var(--muted); font-size: 0.85rem; margin-bottom: 1.25rem; }}
    .grid {{
      display: grid;
      gap: 1rem;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    }}
    .card {{
      background: var(--card);
      border: 1px solid #334155;
      border-radius: 10px;
      padding: 1rem;
    }}
    .kpi {{ font-size: 1.75rem; font-weight: 700; color: var(--accent); }}
    .label {{ color: var(--muted); font-size: 0.8rem; }}
    canvas {{ max-height: 280px; }}
    .foot {{ margin-top: 1.5rem; font-size: 0.75rem; color: var(--muted); }}
    a {{ color: #93c5fd; }}
  </style>
</head>
<body>
  <h1>UK macro — sample KPIs</h1>
  <p class="sub">Static HTML generated from Parquet exports · Built {_escape(now)}</p>
  <div class="grid">
    <div class="card">
      <div class="label">CPIH year-on-year % (latest with value)</div>
      <div class="kpi">{_escape(yoy_display)}</div>
      <div class="label">As of: {_escape(str(metrics.get("cpih_as_of") or "—"))}</div>
    </div>
    <div class="card">
      <div class="label">PSNB (ex. public sector banks), £m — latest month</div>
      <div class="kpi">{_escape(psnb_display)}</div>
      <div class="label">As of: {_escape(str(metrics.get("psnb_as_of") or "—"))}</div>
    </div>
  </div>
  <div class="card" style="margin-top: 1rem;">
    <div class="label">CPIH YoY % (recent months)</div>
    <canvas id="cpihChart"></canvas>
  </div>
  <div class="foot">
    Data: ONS open series (see <code>src/config.py</code>). For CV: import CSVs from
    <code>data/exports/</code> into Excel or Power BI Desktop (free) for richer dashboards.
  </div>
"""

    script = (
        "<script>\n"
        f"const series = {chart_json};\n"
        "const ctx = document.getElementById('cpihChart');\n"
        "new Chart(ctx, {\n"
        "  type: 'line',\n"
        "  data: {\n"
        "    labels: series.labels,\n"
        "    datasets: [{\n"
        "      label: 'YoY %',\n"
        "      data: series.values,\n"
        "      borderColor: '#3b82f6',\n"
        "      backgroundColor: 'rgba(59, 130, 246, 0.15)',\n"
        "      fill: true,\n"
        "      tension: 0.25,\n"
        "    }]\n"
        "  },\n"
        "  options: {\n"
        "    responsive: true,\n"
        "    plugins: { legend: { display: false } },\n"
        "    scales: {\n"
        "      x: { ticks: { maxTicksLimit: 8 }, grid: { color: '#334155' } },\n"
        "      y: { grid: { color: '#334155' } }\n"
        "    }\n"
        "  }\n"
        "});\n"
        "</script>\n"
        "</body>\n</html>\n"
    )
    html = head + script
    output.write_text(html, encoding="utf-8")
    return output


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build static HTML dashboard from exports.")
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output HTML path (default: data/exports/report.html)",
    )
    p.add_argument(
        "--open",
        action="store_true",
        dest="open_browser",
        help="Open the report in the default browser after build",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    base = _export_dir()
    out = build_report(args.output, base=base)
    print(out)
    if args.open_browser:
        webbrowser.open(out.resolve().as_uri())


if __name__ == "__main__":
    main()
