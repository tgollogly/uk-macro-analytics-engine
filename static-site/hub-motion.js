/**
 * Lightweight motion helpers — progressive enhancement only.
 */

export function prefersReducedMotion() {
  return typeof matchMedia !== "undefined" && matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function supportsViewTransitions() {
  return typeof document !== "undefined" && "startViewTransition" in document;
}

/** Cross-document same-origin transitions (Chromium); no-op elsewhere. */
export function initViewTransitionMeta() {
  if (prefersReducedMotion() || !supportsViewTransitions()) return;
  const meta = document.createElement("meta");
  meta.name = "view-transition";
  meta.content = "same-origin";
  if (!document.querySelector('meta[name="view-transition"]')) {
    document.head.appendChild(meta);
  }
}

export function pulseChartContainer(selector) {
  if (prefersReducedMotion()) return;
  const el = document.querySelector(selector);
  const box = el?.closest?.(".chartbox, .chart-wrap") ?? el;
  if (!box) return;
  box.classList.add("is-updating");
  window.setTimeout(() => box.classList.remove("is-updating"), 280);
}

export function markInsightsReady(root = document) {
  root.querySelectorAll?.(".insight-feature[data-insight]").forEach((el) => {
    el.dataset.ready = "true";
  });
}
