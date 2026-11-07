/**
 * Client-side charts from static-site/demo/*.json (pipeline exports).
 * Chart.js 4 — MIT. No fabricated data: all points from JSON.
 */

import {
  CHART_AXIS_TITLE,
  assertLightChartTheme,
  chartJsLightOptions,
  chartUpdateMode,
} from "../chart-light-theme.js";
import { initPageMotion, pulseChartContainer } from "../hub-motion.js";

function cssHubColor(varName, fallback) {
  if (typeof document === "undefined") return fallback;
  const v = getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
  return v || fallback;
}

const CPIH_LINE = cssHubColor("--hub-chart-cpih", "#d64f2a");
const PSNB_LINE = cssHubColor("--hub-chart-psnb", "#0b5e55");

function showErr(msg) {
  const el = document.getElementById("error");
  el.hidden = false;
  el.textContent = msg;
}

function tailSlice(rows, n) {
  if (!rows.length) return [];
  const m = Math.min(n, rows.length);
  return rows.slice(-m);
}

function fmtNum(x, d = 2) {
  if (x === null || x === undefined || Number.isNaN(x)) return "—";
  return Number(x).toLocaleString("en-GB", {
    minimumFractionDigits: d,
    maximumFractionDigits: d,
  });
}

function chartTickBudget() {
  const w = typeof window !== "undefined" ? window.innerWidth : 800;
  if (w < 400) return 5;
  if (w < 640) return 6;
  if (w < 900) return 8;
  return 12;
}

function buildChart(canvas, labels, values, yLabel, borderColor) {
  const ctx = canvas.getContext("2d");
  const fillAlpha = "33";
  const chart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: yLabel,
          data: values,
          borderColor,
          backgroundColor: borderColor + fillAlpha,
          fill: true,
          tension: 0.15,
          spanGaps: false,
          pointRadius: 0,
          borderWidth: 2,
        },
      ],
    },
    options: chartJsLightOptions({
      layout: {
        padding: { left: 4, right: 10, top: 4, bottom: 2 },
      },
      plugins: {
        tooltip: {
          callbacks: {
            title: (items) => items[0]?.label ?? "",
          },
        },
      },
      scales: {
        x: {
          ticks: {
            maxTicksLimit: chartTickBudget(),
          },
        },
        y: {
          title: {
            display: window.innerWidth >= 400,
            text: yLabel,
            color: CHART_AXIS_TITLE,
          },
        },
      },
    }),
  });
  const audit = assertLightChartTheme(chart);
  if (!audit.ok && typeof console !== "undefined") {
    console.warn("chart theme audit", audit);
  }
  return chart;
}

async function loadJson(url) {
  const r = await fetch(url, { cache: "no-store" });
  if (!r.ok) throw new Error(`HTTP ${r.status} for ${url}`);
  return r.json();
}

function main() {
  initPageMotion();
  if (typeof Chart === "undefined") {
    showErr("Chart.js failed to load. Check network or CDN.");
    return;
  }

  let chartCpih = null;
  let chartPsnb = null;

  Promise.all([
    loadJson("./demo/manifest.json"),
    loadJson("./demo/cpih_yoy.json"),
    loadJson("./demo/psnb_monthly.json"),
  ])
    .then(([manifest, cpih, psnb]) => {
      const metaEl = document.getElementById("meta");
      metaEl.innerHTML = "";
      const strong = document.createElement("strong");
      strong.textContent = "Snapshot";
      metaEl.appendChild(strong);
      metaEl.appendChild(
        document.createTextNode(
          ` (UTC): ${manifest.generated_at_utc}. CPIH rows: ${cpih.length}. PSNB rows: ${psnb.length}. `,
        ),
      );
      const span = document.createElement("span");
      span.className = "meta-ons";
      span.textContent = "ONS L522 & DZLS — see manifest for URLs.";
      metaEl.appendChild(span);

      const lim = document.getElementById("limitations");
      lim.innerHTML = "";
      (manifest.limitations || []).forEach((t) => {
        const li = document.createElement("li");
        li.textContent = t;
        lim.appendChild(li);
      });
      const src = document.createElement("li");
      src.className = "prov-src";
      const a1 = document.createElement("a");
      a1.href = manifest.sources.cpih.config_url;
      a1.textContent = "CPIH generator (ONS)";
      a1.rel = "noopener noreferrer";
      const a2 = document.createElement("a");
      a2.href = manifest.sources.psnb.config_url;
      a2.textContent = "PSNB generator (ONS)";
      a2.rel = "noopener noreferrer";
      src.appendChild(document.createTextNode("Sources: "));
      src.appendChild(a1);
      src.appendChild(document.createTextNode(" · "));
      src.appendChild(a2);
      lim.appendChild(src);

      const cpihMonths = document.getElementById("cpih-months");
      const psnbMonths = document.getElementById("psnb-months");
      const cpihVal = document.getElementById("cpih-months-val");
      const psnbVal = document.getElementById("psnb-months-val");

      const canvasCpih = document.getElementById("chart-cpih");
      const canvasPsnb = document.getElementById("chart-psnb");

      function lastValidYoY(rows) {
        for (let i = rows.length - 1; i >= 0; i--) {
          const y = rows[i].yoy_pct;
          if (y !== null && y !== undefined) return { row: rows[i], i };
        }
        return null;
      }

      function lastPsnb(rows) {
        if (!rows.length) return null;
        return rows[rows.length - 1];
      }

      function redrawCpih() {
        const n = parseInt(cpihMonths.value, 10);
        cpihVal.textContent = String(n);
        const slice = tailSlice(cpih, n);
        const labels = slice.map((r) => r.obs_date);
        const vals = slice.map((r) => (r.yoy_pct === null ? null : r.yoy_pct));
        pulseChartContainer("#chart-cpih");
        if (chartCpih) {
          chartCpih.data.labels = labels;
          chartCpih.data.datasets[0].data = vals;
          chartCpih.update(chartUpdateMode());
        } else {
          chartCpih = buildChart(canvasCpih, labels, vals, "YoY %", CPIH_LINE);
        }

        const last = lastValidYoY(slice);
        const k = document.getElementById("cpih-kpi");
        if (last) {
          k.textContent =
            `Latest YoY in window: ${fmtNum(last.row.yoy_pct)}% (${last.row.obs_date}). ` +
            `Missing early months are expected until 12 lags exist.`;
        } else {
          k.textContent = "No YoY values in the selected window.";
        }
      }

      function redrawPsnb() {
        const n = parseInt(psnbMonths.value, 10);
        psnbVal.textContent = String(n);
        const slice = tailSlice(psnb, n);
        const labels = slice.map((r) => r.obs_date);
        const vals = slice.map((r) => r.total_net_borrowing_gbp_m);
        pulseChartContainer("#chart-psnb");
        if (chartPsnb) {
          chartPsnb.data.labels = labels;
          chartPsnb.data.datasets[0].data = vals;
          chartPsnb.update(chartUpdateMode());
        } else {
          chartPsnb = buildChart(canvasPsnb, labels, vals, "£m", PSNB_LINE);
        }

        const last = lastPsnb(slice);
        const k = document.getElementById("psnb-kpi");
        if (last) {
          const rc = last.row_count;
          const extra = rc && rc > 1 ? ` (${rc} CSV rows summed that month).` : ".";
          k.textContent = `Latest PSNB: £${fmtNum(last.total_net_borrowing_gbp_m, 0)}m (${last.obs_date})${extra}`;
        } else {
          k.textContent = "No PSNB rows.";
        }
      }

      function resizeCharts() {
        if (chartCpih) {
          chartCpih.options.scales.x.ticks.maxTicksLimit = chartTickBudget();
          chartCpih.options.scales.y.title.display = window.innerWidth >= 400;
          chartCpih.update("none");
        }
        if (chartPsnb) {
          chartPsnb.options.scales.x.ticks.maxTicksLimit = chartTickBudget();
          chartPsnb.options.scales.y.title.display = window.innerWidth >= 400;
          chartPsnb.update("none");
        }
      }

      cpihMonths.addEventListener("input", redrawCpih);
      psnbMonths.addEventListener("input", redrawPsnb);
      cpihMonths.max = String(Math.min(240, cpih.length));
      psnbMonths.max = String(Math.min(240, psnb.length));

      redrawCpih();
      redrawPsnb();
      window.addEventListener("resize", () => {
        window.requestAnimationFrame(resizeCharts);
      });
    })
    .catch((e) => {
      showErr(`Failed to load demo data: ${e.message}`);
      document.getElementById("meta").textContent = "Manifest unavailable.";
    });
}

document.addEventListener("DOMContentLoaded", main);
