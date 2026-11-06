/**
 * Client-side charts from static-site/demo/*.json (pipeline exports).
 * Chart.js 4 — MIT. No fabricated data: all points from JSON.
 */

const CP = "#38bdf8";
const PS = "#a78bfa";

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

function buildChart(canvas, labels, values, yLabel, borderColor) {
  const ctx = canvas.getContext("2d");
  return new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: yLabel,
          data: values,
          borderColor,
          backgroundColor: borderColor + "22",
          fill: true,
          tension: 0.15,
          spanGaps: false,
          pointRadius: 0,
          borderWidth: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { labels: { color: "#e2e8f0" } },
        tooltip: {
          callbacks: {
            title: (items) => items[0]?.label ?? "",
          },
        },
      },
      scales: {
        x: {
          ticks: { color: "#94a3b8", maxRotation: 45, minRotation: 0 },
          grid: { color: "#334155" },
        },
        y: {
          ticks: { color: "#94a3b8" },
          grid: { color: "#334155" },
          title: { display: true, text: yLabel, color: "#cbd5e1" },
        },
      },
    },
  });
}

async function loadJson(url) {
  const r = await fetch(url, { cache: "no-store" });
  if (!r.ok) throw new Error(`HTTP ${r.status} for ${url}`);
  return r.json();
}

function main() {
  if (typeof Chart === "undefined") {
    showErr("Chart.js failed to load. Check network or CDN.");
    return;
  }

  Promise.all([
    loadJson("./demo/manifest.json"),
    loadJson("./demo/cpih_yoy.json"),
    loadJson("./demo/psnb_monthly.json"),
  ])
    .then(([manifest, cpih, psnb]) => {
      document.getElementById("meta").textContent =
        `Snapshot generated (UTC): ${manifest.generated_at_utc} · ` +
        `CPIH rows: ${cpih.length} · PSNB rows: ${psnb.length} · ` +
        `ONS L522 & DZLS — see manifest for URLs.`;

      const lim = document.getElementById("limitations");
      lim.innerHTML = "";
      (manifest.limitations || []).forEach((t) => {
        const li = document.createElement("li");
        li.textContent = t;
        lim.appendChild(li);
      });
      const src = document.createElement("li");
      src.innerHTML = `<strong>CPIH:</strong> <a href="${manifest.sources.cpih.config_url}" style="color:#93c5fd">generator URL</a> · ` +
        `<strong>PSNB:</strong> <a href="${manifest.sources.psnb.config_url}" style="color:#93c5fd">generator URL</a>`;
      lim.appendChild(src);

      const cpihMonths = document.getElementById("cpih-months");
      const psnbMonths = document.getElementById("psnb-months");
      const cpihVal = document.getElementById("cpih-months-val");
      const psnbVal = document.getElementById("psnb-months-val");

      const canvasCpih = document.getElementById("chart-cpih");
      const canvasPsnb = document.getElementById("chart-psnb");

      let chartCpih = null;
      let chartPsnb = null;

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
        if (chartCpih) chartCpih.destroy();
        chartCpih = buildChart(canvasCpih, labels, vals, "YoY %", CP);

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
        if (chartPsnb) chartPsnb.destroy();
        chartPsnb = buildChart(canvasPsnb, labels, vals, "£m", PS);

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

      cpihMonths.addEventListener("input", redrawCpih);
      psnbMonths.addEventListener("input", redrawPsnb);
      cpihMonths.max = String(Math.min(240, cpih.length));
      psnbMonths.max = String(Math.min(240, psnb.length));

      redrawCpih();
      redrawPsnb();
    })
    .catch((e) => {
      showErr(`Failed to load demo data: ${e.message}`);
      document.getElementById("meta").textContent = "Manifest unavailable.";
    });
}

document.addEventListener("DOMContentLoaded", main);
