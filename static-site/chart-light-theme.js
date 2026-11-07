/**
 * Chart.js colours for light (ivory) shell — WCAG-friendly on white card backgrounds.
 * Import from demo pages and macro-explorer; do not use dark-theme slate legend ticks.
 */

export const CHART_LEGEND = "#1a2332";
export const CHART_TICK = "#4a5568";
export const CHART_GRID = "#c8cdd4";
export const CHART_AXIS_TITLE = "#1a2332";

/** Align with static-site/hub-tokens.css — CPIH coral, PSNB teal fiscal. */
export const CHART_SERIES_CPIH = "#d64f2a";
export const CHART_SERIES_PSNB = "#0b5e55";

export function prefersReducedMotion() {
  if (typeof window === "undefined" || !window.matchMedia) return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/** Chart.js update mode: animated when motion allowed. */
export function chartUpdateMode() {
  return prefersReducedMotion() ? "none" : "active";
}

export function chartMotionMs() {
  return prefersReducedMotion() ? 0 : 750;
}

/** @param {import('chart.js').ChartConfiguration['options']} [extra] */
export function chartJsLightOptions(extra = {}) {
  const duration = chartMotionMs();
  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    animation: duration
      ? { duration }
      : { duration: 0 },
    transitions: {
      active: { animation: { duration } },
      resize: { animation: { duration: prefersReducedMotion() ? 0 : 280 } },
    },
    plugins: {
      legend: { labels: { color: CHART_LEGEND, boxWidth: 14 } },
      tooltip: {
        titleColor: CHART_LEGEND,
        bodyColor: CHART_AXIS_TITLE,
        backgroundColor: "rgba(255, 255, 255, 0.96)",
        borderColor: CHART_GRID,
        borderWidth: 1,
      },
      ...extra.plugins,
    },
    scales: {
      x: {
        ticks: {
          color: CHART_TICK,
          maxRotation: 45,
          minRotation: 0,
          autoSkip: true,
          ...extra.scales?.x?.ticks,
        },
        grid: { color: CHART_GRID, ...extra.scales?.x?.grid },
        ...extra.scales?.x,
      },
      y: {
        ticks: { color: CHART_TICK, ...extra.scales?.y?.ticks },
        grid: { color: CHART_GRID, ...extra.scales?.y?.grid },
        title: {
          display: false,
          color: CHART_AXIS_TITLE,
          ...extra.scales?.y?.title,
        },
        ...extra.scales?.y,
      },
    },
    ...(extra.layout ? { layout: extra.layout } : {}),
  };
}

/**
 * Regression guard: assert Chart instance uses light-theme label colours after build.
 * @param {import('chart.js').Chart | null | undefined} chart
 */
export function assertLightChartTheme(chart) {
  if (!chart?.options) return { ok: false, reason: "no chart" };
  const leg =
    chart.options.plugins?.legend?.labels?.color ??
    chart.config?.options?.plugins?.legend?.labels?.color;
  const xTick = chart.options.scales?.x?.ticks?.color;
  const yTick = chart.options.scales?.y?.ticks?.color;
  const problems = [];
  if (leg && leg.toLowerCase() === "#e2e8f0") problems.push("legend still dark-era #e2e8f0");
  if (xTick && String(xTick).toLowerCase() === "#94a3b8") problems.push("x ticks still #94a3b8");
  if (yTick && String(yTick).toLowerCase() === "#94a3b8") problems.push("y ticks still #94a3b8");
  return { ok: problems.length === 0, problems, leg, xTick, yTick };
}
