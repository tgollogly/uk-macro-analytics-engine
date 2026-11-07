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
  const boxes = [
    ...new Set(
      [...document.querySelectorAll(selector)].map(
        (el) => el.closest?.(".chartbox, .chart-wrap") ?? el,
      ),
    ),
  ];
  for (const box of boxes) {
    if (!box) continue;
    box.classList.remove("motion-chart-pulse");
    void box.offsetWidth;
    box.classList.add("motion-chart-pulse");
    box.addEventListener(
      "animationend",
      () => box.classList.remove("motion-chart-pulse"),
      { once: true },
    );
  }
}

export function markInsightsReady(root = document) {
  root.querySelectorAll?.(".insight-feature[data-insight]").forEach((el) => {
    el.dataset.ready = "true";
  });
  const hero = root.querySelector?.(".hero");
  if (hero) hero.classList.add("is-data-live");
}

/** Scroll-linked emphasis on insight cards (no parallax / scroll-jacking). */
/** Section reveal when panels enter viewport (no parallax). */
export function initSectionReveal(selector = ".reveal-section", root = document) {
  const nodes = root.querySelectorAll?.(selector);
  if (!nodes?.length) return;
  if (prefersReducedMotion()) {
    nodes.forEach((n) => n.classList.add("is-visible"));
    return;
  }
  const io = new IntersectionObserver(
    (entries) => {
      for (const e of entries) {
        if (e.isIntersecting) {
          e.target.classList.add("is-visible");
          io.unobserve(e.target);
        }
      }
    },
    { rootMargin: "-8% 0px -6% 0px", threshold: 0.12 },
  );
  nodes.forEach((n) => io.observe(n));
}

export function setAsyncLoadState(root, state, message = "") {
  const el = typeof root === "string" ? document.querySelector(root) : root;
  if (!el) return;
  el.setAttribute("data-load-state", state);
  const status = el.querySelector?.("[data-async-status]");
  if (status) {
    status.textContent = message;
    status.dataset.tone = state === "error" ? "error" : "neutral";
  }
}

export function initStoryScrollEmphasis(root = document) {
  if (prefersReducedMotion()) return;
  const cards = root.querySelectorAll?.(".insight-feature[data-insight]");
  if (!cards?.length) return;
  const io = new IntersectionObserver(
    (entries) => {
      for (const e of entries) {
        e.target.classList.toggle("story-in-view", e.isIntersecting);
      }
    },
    { rootMargin: "-15% 0px -15% 0px", threshold: 0.35 },
  );
  cards.forEach((c) => io.observe(c));
}
