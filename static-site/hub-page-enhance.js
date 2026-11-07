/**
 * Shared async boot for story pages — honest loading states, no fake delay.
 */
import {
  initPageMotion,
  initSectionReveal,
  pulseChartContainer,
  setAsyncLoadState,
} from "./hub-motion.js";

export async function bootDataPage({ rootSelector = "[data-async-root]", load }) {
  initPageMotion();
  initSectionReveal(".reveal-section");
  const root = document.querySelector(rootSelector);
  setAsyncLoadState(root, "loading", "Loading snapshot charts…");
  try {
    await load();
    setAsyncLoadState(root, "ready", "");
    document.body.classList.add("page-data-ready");
    document.body.dataset.pageReady = "true";
    pulseChartContainer(".chartbox, .ms-chart, .cs-chart");
  } catch (err) {
    setAsyncLoadState(
      root,
      "error",
      err instanceof Error ? err.message : "Could not load snapshot data.",
    );
    throw err;
  }
}
