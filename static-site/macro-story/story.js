/**
 * Monthly macro visual story — macro-story.json only (snapshot).
 */
import { bootDataPage } from "../hub-page-enhance.js?v=20251107d4";
import { chartJsLightOptions, chartMotionMs } from "../chart-light-theme.js?v=20251107d2";

const HEAT_STEPS = [
  { bg: "#d8efe8", fg: "#0b3d3a", label: "low" },
  { bg: "#9fd4c7", fg: "#0b3d3a", label: "" },
  { bg: "#f5d4a5", fg: "#1a2332", label: "" },
  { bg: "#e8925c", fg: "#1a2332", label: "" },
  { bg: "#c7502e", fg: "#fff", label: "high" },
];

const PALETTE = {
  coral: "#d64f2a",
  teal: "#0b5e55",
  amber: "#c17f3a",
  neg: "#7c1d4d",
};

async function loadStory() {
  const res = await fetch("../demo/macro-story.json");
  if (!res.ok) throw new Error(`macro-story HTTP ${res.status}`);
  return res.json();
}

function heatCellStyle(v, vmin, vmax) {
  const t = vmax === vmin ? 0.5 : (v - vmin) / (vmax - vmin);
  const idx = Math.min(HEAT_STEPS.length - 1, Math.max(0, Math.floor(t * HEAT_STEPS.length)));
  return HEAT_STEPS[idx];
}

function paintHeatmap(root, heatmap) {
  const years = [...new Set(heatmap.cells.map((c) => c.year))].sort();
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const lookup = new Map(heatmap.cells.map((c) => [`${c.year}-${c.month}`, c.yoy_pct]));
  const vals = heatmap.cells.map((c) => c.yoy_pct);
  const vmin = Math.min(...vals);
  const vmax = Math.max(...vals);
  const table = document.createElement("table");
  table.className = "ms-heatmap";
  table.setAttribute("role", "grid");
  table.setAttribute(
    "aria-label",
    `${heatmap.title}. Values are year-on-year inflation rates in percent.`,
  );
  const thead = document.createElement("thead");
  const hr = document.createElement("tr");
  hr.appendChild(document.createElement("th")).textContent = "Year";
  months.forEach((m) => {
    const th = document.createElement("th");
    th.scope = "col";
    th.textContent = m;
    hr.appendChild(th);
  });
  thead.appendChild(hr);
  table.appendChild(thead);
  const tbody = document.createElement("tbody");
  years.forEach((y) => {
    const tr = document.createElement("tr");
    const th = document.createElement("th");
    th.scope = "row";
    th.textContent = String(y);
    tr.appendChild(th);
    for (let m = 1; m <= 12; m += 1) {
      const td = document.createElement("td");
      const v = lookup.get(`${y}-${m}`);
      if (v == null) {
        td.textContent = "—";
        td.dataset.empty = "true";
      } else {
        const style = heatCellStyle(v, vmin, vmax);
        td.textContent = `${v.toFixed(1)}%`;
        td.style.background = style.bg;
        td.style.color = style.fg;
        td.title = `${y}-${String(m).padStart(2, "0")}: ${v.toFixed(2)}% YoY CPIH rate`;
      }
      tr.appendChild(td);
    }
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  root.replaceChildren(table);
  const leg = document.createElement("p");
  leg.className = "ms-legend";
  leg.textContent =
    `CPIH YoY % from ${heatmap.year_from}. ${heatmap.legend} ` +
    `Scale ${vmin.toFixed(1)}% (teal) → ${vmax.toFixed(1)}% (coral).`;
  root.appendChild(leg);
}

function chartBoxOptions(extra = {}) {
  return chartJsLightOptions({
    maintainAspectRatio: false,
    responsive: true,
    layout: { padding: { top: 8, right: 12, left: 4, bottom: 4 } },
    ...extra,
  });
}

function cpihLineChart(canvas, points, turning) {
  const labels = points.map((p) => p.month);
  const data = points.map((p) => p.yoy_pct);
  const turnMonths = new Set(turning.map((t) => t.month));
  return new Chart(canvas, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "CPIH YoY %",
          data,
          borderColor: PALETTE.coral,
          backgroundColor: PALETTE.coral + "28",
          fill: true,
          tension: 0.28,
          pointRadius: labels.map((m) => (turnMonths.has(m) ? 8 : 4)),
          pointBackgroundColor: labels.map((m) =>
            turnMonths.has(m) ? PALETTE.amber : PALETTE.coral,
          ),
          borderWidth: 2.5,
        },
      ],
    },
    options: chartBoxOptions({
      plugins: {
        legend: { display: true },
        tooltip: {
          callbacks: {
            label: (ctx) => `YoY ${ctx.parsed.y?.toFixed(2)}% (rate, not price level)`,
          },
        },
      },
      scales: {
        x: { ticks: { maxTicksLimit: 8, maxRotation: 0 } },
        y: {
          title: { display: true, text: "YoY % inflation rate" },
          ticks: { callback: (v) => `${v}%` },
        },
      },
      animation: { duration: chartMotionMs() },
    }),
  });
}

function psnbBarChart(canvas, bars) {
  return new Chart(canvas, {
    type: "bar",
    data: {
      labels: bars.map((b) => b.month),
      datasets: [
        {
          label: "PSNB monthly (£m)",
          data: bars.map((b) => b.borrowing_gbp_m),
          backgroundColor: bars.map((b) =>
            b.borrowing_gbp_m >= 0 ? PALETTE.teal : PALETTE.neg,
          ),
          borderRadius: 8,
          maxBarThickness: 40,
        },
      ],
    },
    options: chartBoxOptions({
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => `£${ctx.parsed.y?.toLocaleString("en-GB")}m borrowing`,
          },
        },
      },
      scales: {
        x: { ticks: { maxTicksLimit: 8, maxRotation: 0 } },
        y: {
          title: { display: true, text: "£ million (monthly)" },
          ticks: {
            maxTicksLimit: 6,
            callback: (v) => `£${Number(v).toLocaleString("en-GB")}m`,
          },
        },
      },
      animation: { duration: chartMotionMs() },
    }),
  });
}

function renderFindings(host, findings) {
  host.replaceChildren(
    ...findings.map((f) => {
      const art = document.createElement("article");
      art.className = "ms-finding hub-story-card";
      art.innerHTML = `<p class="ms-tag">${f.series}</p>
        <h3>${f.headline}</h3>
        <p>${f.detail}</p>
        <p class="ms-limit"><strong>Does not prove:</strong> ${f.does_not_prove}</p>
        <p class="ms-meta">${f.period} · ${f.units}</p>`;
      return art;
    }),
  );
}

async function renderStory() {
  const story = await loadStory();
  document.getElementById("story-asof").textContent =
    `Snapshot ${story.snapshot_manifest_utc ?? "—"} UTC · bundle ${story.generated_at_utc}`;
  paintHeatmap(document.getElementById("heatmap-host"), story.cpih_heatmap);
  cpihLineChart(
    document.getElementById("chart-cpih"),
    story.cpih_yoy_last_24m,
    story.cpih_turning_points_24m,
  );
  psnbBarChart(document.getElementById("chart-psnb"), story.psnb_monthly_last_24m);
  const fy = story.psnb_fy_partial_compare;
  if (fy?.available) {
    document.getElementById("fy-compare").hidden = false;
    document.getElementById("fy-text").textContent =
      `${fy.current_fy_label} through ${fy.through_month}: £${fy.cumulative_borrowing_gbp_m_current.toLocaleString("en-GB")}m vs ${fy.prior_fy_label}: £${fy.cumulative_borrowing_gbp_m_prior_matched.toLocaleString("en-GB")}m. ${fy.note}`;
  }
  renderFindings(document.getElementById("findings-grid"), story.findings);
  const tp = document.getElementById("turning-list");
  if (tp) {
    tp.replaceChildren(
      ...story.cpih_turning_points_24m.map((t) => {
        const li = document.createElement("li");
        li.textContent =
          `${t.kind === "local_peak" ? "Peak" : "Trough"} ${t.month}: ${t.yoy_pct}% ` +
          `(MoM ${t.mom_change_pp >= 0 ? "+" : ""}${t.mom_change_pp} pp)`;
        return li;
      }),
    );
  }
  document.querySelectorAll(".chartbox").forEach((el) => {
    el.dataset.chartReady = "true";
  });
}

bootDataPage({ load: renderStory });
