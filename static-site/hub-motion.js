/**
 * Safari-compatible motion — class-triggered CSS + Chart pulse; no hidden content.
 */

export function prefersReducedMotion() {
  return typeof matchMedia !== "undefined" && matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function supportsViewTransitions() {
  return typeof document !== "undefined" && "startViewTransition" in document;
}

export function initViewTransitionMeta() {
  if (prefersReducedMotion() || !supportsViewTransitions()) return;
  if (!document.querySelector('meta[name="view-transition"]')) {
    const meta = document.createElement("meta");
    meta.name = "view-transition";
    meta.content = "same-origin";
    document.head.appendChild(meta);
  }
}

/** Enable perceptible entrances after first paint (content already visible in HTML). */
export function initPageMotion() {
  initViewTransitionMeta();
  if (prefersReducedMotion()) return;
  const run = () => {
    if (document.body) document.body.classList.add("is-motion-on");
  };
  run();
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", run, { once: true });
  }
  requestAnimationFrame(() => requestAnimationFrame(run));
}

export function pulseChartContainer(selector) {
  if (prefersReducedMotion()) return;
  const el = document.querySelector(selector);
  const box = el?.closest?.(".chartbox, .chart-wrap") ?? el;
  if (!box) return;
  box.classList.remove("motion-chart-pulse");
  void box.offsetWidth;
  box.classList.add("motion-chart-pulse");
  box.addEventListener(
    "animationend",
    () => box.classList.remove("motion-chart-pulse"),
    { once: true },
  );
}

export function markInsightsReady(root = document) {
  root.querySelectorAll?.(".insight-feature[data-insight]").forEach((el) => {
    el.dataset.ready = "true";
  });
}
