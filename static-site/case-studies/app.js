/**
 * Case study charts — loads committed summary JSON only (no live APIs).
 */
import { bootDataPage } from "../hub-page-enhance.js?v=20251107d4";
import { chartJsLightOptions } from "../chart-light-theme.js";
import { chartMotionMs } from "../chart-light-theme.js";

const fmtM = (n) =>
  new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP",
    maximumFractionDigits: 0,
    notation: Math.abs(n) >= 1_000_000 ? "compact" : "standard",
  }).format(n);
const fmtBn = (n) => `£${n.toFixed(2)}bn`;

const chartBoxOptions = (extra = {}) =>
  chartJsLightOptions({
    maintainAspectRatio: false,
    responsive: true,
    layout: { padding: { top: 4, right: 4, left: 4, bottom: 4 } },
    ...extra,
  });

async function loadJson(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Failed ${path}`);
  return res.json();
}

function niChart(canvas, data) {
  const actual = data.actual_cost_gbp;
  const gross = data.gross_cost_gbp;
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
          maxBarThickness: 64,
        },
      ],
    },
    options: chartBoxOptions({
      animation: { duration: chartMotionMs() },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => fmtM(ctx.parsed.y),
          },
        },
      },
      scales: {
        x: { ticks: { maxRotation: 0, autoSkip: true } },
        y: {
          ticks: {
            maxTicksLimit: 5,
            callback: (v) => fmtM(v),
          },
        },
      },
    }),
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
          maxBarThickness: 72,
        },
      ],
    },
    options: chartBoxOptions({
      animation: { duration: chartMotionMs() },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => fmtBn(ctx.parsed.y),
          },
        },
      },
      scales: {
        x: { ticks: { maxRotation: 0 } },
        y: {
          title: { display: true, text: "£ billion" },
          ticks: { maxTicksLimit: 5 },
        },
      },
    }),
  });
}

async function renderCaseStudies() {
  const [ni, trade] = await Promise.all([
    loadJson("./case-studies/ni-prescribing-2026-08-summary.json"),
    loadJson("./case-studies/uk-energy-trade-q2-2026-summary.json"),
  ]);

  const niCanvas = document.getElementById("chart-ni-costs");
  const tradeCanvas = document.getElementById("chart-trade-crude");
  if (niCanvas) niChart(niCanvas, ni);
  if (tradeCanvas) tradeChart(tradeCanvas, trade);

  const niCap = document.getElementById("ni-chart-caption");
  if (niCap) {
    niCap.textContent = `${ni.total_items.toLocaleString("en-GB")} prescription items (not patients).`;
  }
  const trCap = document.getElementById("trade-chart-caption");
  if (trCap) {
    trCap.textContent = `YoY change (CPA 06.1): +${trade.cpa_crude_exports.yoy_change_pct}%.`;
  }

  const niFig = document.getElementById("ni-findings");
  if (niFig) {
    niFig.textContent = `${ni.distinct_practices} GP practices; ${ni.total_items.toLocaleString("en-GB")} items; actual ${fmtM(ni.actual_cost_gbp)}.`;
  }
  const trFig = document.getElementById("trade-findings");
  if (trFig) {
    trFig.textContent = `Crude exports ${fmtBn(trade.cpa_crude_exports.prior_q_gbp_b)} → ${fmtBn(trade.cpa_crude_exports.current_q_gbp_b)} (CPA 06.1, current prices).`;
  }
  document.querySelectorAll(".chartbox").forEach((el) => {
    el.dataset.chartReady = "true";
  });
}

bootDataPage({ load: renderCaseStudies });
