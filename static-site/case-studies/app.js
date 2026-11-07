/**
 * Case study charts — loads committed summary JSON only (no live APIs).
 */
import { chartJsLightOptions } from "../chart-light-theme.js";

const fmtM = (n) =>
  new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP", maximumFractionDigits: 0 }).format(n);
const fmtBn = (n) => `£${n.toFixed(2)}bn`;

async function loadJson(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Failed ${path}`);
  return res.json();
}

function niChart(canvas, data) {
  const actual = data.actual_cost_gbp;
  const gross = data.gross_cost_gbp;
  const items = data.total_items;
  return new Chart(canvas, {
    type: "bar",
    data: {
      labels: ["Actual cost", "Gross (list) cost"],
      datasets: [
        {
          label: "August 2026 NI GP prescribing (£)",
          data: [actual, gross],
          backgroundColor: ["#1d5c8c", "#e8a830"],
          borderRadius: 8,
        },
      ],
    },
    options: chartJsLightOptions({
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => fmtM(ctx.parsed.y),
          },
        },
      },
      scales: {
        y: {
          ticks: {
            callback: (v) => fmtM(v),
          },
        },
      },
    }),
    plugins: [
      {
        id: "niKpi",
        afterDraw(chart) {
          const { ctx, chartArea } = chart;
          ctx.save();
          ctx.font = "600 13px Inter, system-ui, sans-serif";
          ctx.fillStyle = "#334155";
          ctx.fillText(
            `${items.toLocaleString("en-GB")} prescription items (not patients)`,
            chartArea.left,
            chartArea.bottom + 28
          );
          ctx.restore();
        },
      },
    ],
  });
}

function tradeChart(canvas, data) {
  const crude = data.cpa_crude_exports;
  return new Chart(canvas, {
    type: "bar",
    data: {
      labels: ["Q2 2025", "Q2 2026"],
      datasets: [
        {
          label: "CPA 06.1 Crude petroleum exports (CP, £bn)",
          data: [crude.prior_q_gbp_b, crude.current_q_gbp_b],
          backgroundColor: ["#7c3aed", "#14b8a6"],
          borderRadius: 8,
        },
      ],
    },
    options: chartJsLightOptions({
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => fmtBn(ctx.parsed.y),
          },
        },
      },
      scales: {
        y: {
          title: { display: true, text: "£ billion" },
        },
      },
    }),
    plugins: [
      {
        id: "tradeYoY",
        afterDraw(chart) {
          const yoy = crude.yoy_change_pct;
          const { ctx, chartArea } = chart;
          ctx.save();
          ctx.font = "600 13px Inter, system-ui, sans-serif";
          ctx.fillStyle = "#334155";
          ctx.fillText(
            `YoY change (same CPA row): +${yoy}%`,
            chartArea.left,
            chartArea.bottom + 28
          );
          ctx.restore();
        },
      },
    ],
  });
}

export async function initCaseStudyCharts() {
  const [ni, trade] = await Promise.all([
    loadJson("./case-studies/ni-prescribing-2026-08-summary.json"),
    loadJson("./case-studies/uk-energy-trade-q2-2026-summary.json"),
  ]);

  const niCanvas = document.getElementById("chart-ni-costs");
  const tradeCanvas = document.getElementById("chart-trade-crude");
  if (niCanvas) niChart(niCanvas, ni);
  if (tradeCanvas) tradeChart(tradeCanvas, trade);

  const niFig = document.getElementById("ni-findings");
  if (niFig) {
    niFig.textContent = `${ni.distinct_practices} GP practices; ${ni.total_items.toLocaleString("en-GB")} items; actual ${fmtM(ni.actual_cost_gbp)}.`;
  }
  const trFig = document.getElementById("trade-findings");
  if (trFig) {
    trFig.textContent = `Crude exports ${fmtBn(trade.cpa_crude_exports.prior_q_gbp_b)} → ${fmtBn(trade.cpa_crude_exports.current_q_gbp_b)} (CPA 06.1, current prices).`;
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => initCaseStudyCharts().catch(console.error));
} else {
  initCaseStudyCharts().catch(console.error);
}
