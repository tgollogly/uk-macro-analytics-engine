/**
 * Static macro demos — load committed pipeline JSON under ../demo/ (snapshot, not live ONS).
 */
const MACRO_MANIFEST = new URL("../../demo/manifest.json", import.meta.url);
const CPIH_URL = new URL("../../demo/cpih_yoy.json", import.meta.url);
const PSNB_URL = new URL("../../demo/psnb_monthly.json", import.meta.url);

function cssHubColor(varName, fallback) {
  if (typeof document === "undefined") return fallback;
  const v = getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
  return v || fallback;
}

export const CPIH_LINE = cssHubColor("--hub-chart-cpih", "#d64f2a");
export const PSNB_LINE = cssHubColor("--hub-chart-psnb", "#0b5e55");

/** Max rows shown in macro-explorer table; chart + CSV use the full filtered range. */
export const TABLE_PREVIEW_LIMIT = 24;

export function sliceTablePreview(rows, limit = TABLE_PREVIEW_LIMIT) {
  const total = rows.length;
  if (total === 0) {
    return { total: 0, display: [], capped: false, displayCount: 0 };
  }
  if (total <= limit) {
    return { total, display: [...rows].reverse(), capped: false, displayCount: total };
  }
  return {
    total,
    display: rows.slice(-limit).reverse(),
    capped: true,
    displayCount: limit,
  };
}

export async function loadMacroBundle() {
  const [manifest, cpih, psnb] = await Promise.all([
    fetch(MACRO_MANIFEST).then((r) => {
      if (!r.ok) throw new Error(`manifest HTTP ${r.status}`);
      return r.json();
    }),
    fetch(CPIH_URL).then((r) => {
      if (!r.ok) throw new Error(`cpih_yoy HTTP ${r.status}`);
      return r.json();
    }),
    fetch(PSNB_URL).then((r) => {
      if (!r.ok) throw new Error(`psnb_monthly HTTP ${r.status}`);
      return r.json();
    }),
  ]);
  if (!Array.isArray(cpih) || !Array.isArray(psnb)) throw new Error("Expected JSON arrays");
  return { manifest, cpih, psnb };
}

export function parseMonth(s) {
  const t = Date.parse(s + (s.length === 10 ? "T00:00:00Z" : ""));
  return Number.isFinite(t) ? t : NaN;
}

export function monthInputToMs(v) {
  if (!v) return null;
  const [y, m] = v.split("-").map(Number);
  return Date.UTC(y, m - 1, 1);
}

export function monthLabelFromRow(row) {
  return row?.obs_date?.slice(0, 7) ?? null;
}

/**
 * Window presets slice the series; custom range uses From/To only when window is "all".
 */
export function selectExplorerRows(base, { windowValue, fromMonth, toMonth }) {
  const fromMs = monthInputToMs(fromMonth);
  const toMs = monthInputToMs(toMonth);
  if (windowValue !== "all" && windowValue != null && String(windowValue) !== "") {
    const n = Number(windowValue);
    const rows = Number.isFinite(n) && n > 0 ? base.slice(-n) : [...base];
    return {
      rows,
      mode: "window",
      effectiveFrom: monthLabelFromRow(rows[0]),
      effectiveTo: monthLabelFromRow(rows[rows.length - 1]),
    };
  }
  const rows = filterByRange(base, fromMs, toMs);
  return {
    rows,
    mode: "range",
    effectiveFrom: monthLabelFromRow(rows[0]),
    effectiveTo: monthLabelFromRow(rows[rows.length - 1]),
  };
}

export function filterByRange(rows, fromMs, toMs, dateKey = "obs_date") {
  return rows.filter((row) => {
    const t = parseMonth(row[dateKey]);
    if (!Number.isFinite(t)) return false;
    if (fromMs != null && t < fromMs) return false;
    if (toMs != null && t > toMs) return false;
    return true;
  });
}

export function countNullYoy(cpih) {
  return cpih.reduce((n, r) => n + (r.yoy_pct == null ? 1 : 0), 0);
}

export function psnbMultiRowMonths(psnb) {
  return psnb.filter((r) => (r.row_count ?? 1) > 1);
}

/** Expected monthly steps (UTC); returns { missing: string[], gaps: string[] } for CPIH. */
export function findMonthGaps(rows, dateKey = "obs_date") {
  const sorted = [...rows]
    .map((r) => r[dateKey])
    .filter(Boolean)
    .sort();
  const missing = [];
  const gaps = [];
  for (let i = 1; i < sorted.length; i++) {
    const a = parseMonth(sorted[i - 1]);
    const b = parseMonth(sorted[i]);
    if (!Number.isFinite(a) || !Number.isFinite(b)) continue;
    const expect = new Date(a);
    expect.setUTCMonth(expect.getUTCMonth() + 1);
    const expectIso = expect.toISOString().slice(0, 10);
    const actual = sorted[i].slice(0, 10);
    if (actual !== expectIso && b - a > 32 * 86400000) {
      gaps.push(`${sorted[i - 1].slice(0, 7)} → ${sorted[i].slice(0, 7)}`);
    }
  }
  return { missing, gaps };
}

export function rowsToCsv(rows, columns) {
  const esc = (v) => {
    if (v == null) return "";
    const s = String(v);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const head = columns.join(",");
  const body = rows.map((r) => columns.map((c) => esc(r[c])).join(",")).join("\n");
  return head + "\n" + body + "\n";
}

export function downloadText(filename, text, mime = "text/csv;charset=utf-8") {
  const blob = new Blob([text], { type: mime });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

export function fmtPct(x) {
  if (x == null || Number.isNaN(x)) return "—";
  return Number(x).toLocaleString("en-GB", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + "%";
}

export function fmtGbpM(x) {
  if (x == null || Number.isNaN(x)) return "—";
  return (
    "£" +
    Number(x).toLocaleString("en-GB", { minimumFractionDigits: 0, maximumFractionDigits: 0 }) +
    "m"
  );
}
