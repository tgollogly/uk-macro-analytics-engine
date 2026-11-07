#!/usr/bin/env node
/**
 * Visual polish QA — motion hooks, async ready, overflow, chart ready flags.
 * Usage: node tools/visual_polish_qa.mjs <baseUrl>
 */
import { chromium } from "playwright";
import { mkdirSync, writeFileSync } from "node:fs";

const base = (process.argv[2] || "http://127.0.0.1:8765").replace(/\/$/, "");
const ART = process.env.VISUAL_POLISH_QA_ARTIFACT_DIR || "/opt/cursor/artifacts";

const PAGES = [
  { path: "/macro-story.html", root: "[data-async-root]", charts: ".chartbox" },
  { path: "/case-studies.html", root: "[data-async-root]", charts: ".chartbox" },
];

async function auditPage(page, spec, vpName, w, h) {
  await page.setViewportSize({ width: w, height: h });
  await page.goto(`${base}${spec.path}`, { waitUntil: "networkidle", timeout: 45_000 });
  await page.waitForFunction(
    () => document.body?.dataset?.pageReady === "true",
    { timeout: 20_000 },
  );
  const metrics = await page.evaluate(({ rootSel, chartSel }) => {
    const doc = document.documentElement;
    const root = document.querySelector(rootSel);
    const charts = [...document.querySelectorAll(chartSel)];
    const reveals = [...document.querySelectorAll(".reveal-section")];
    return {
      motionOn: document.body.classList.contains("is-motion-on"),
      pageReady: document.body.dataset.pageReady === "true",
      loadState: root?.getAttribute("data-load-state") ?? null,
      docOverflow: doc.scrollWidth > doc.clientWidth + 1,
      docScroll: doc.scrollWidth,
      docClient: doc.clientWidth,
      chartsReady: charts.every((c) => c.dataset.chartReady === "true"),
      chartCount: charts.length,
      revealsVisible: reveals.filter((n) => n.classList.contains("is-visible")).length,
      revealCount: reveals.length,
      consoleErrors: window.__qaConsoleErrors ?? [],
    };
  }, { rootSel: spec.root, chartSel: spec.charts });
  mkdirSync(ART, { recursive: true });
  const slug = spec.path.replace(/\//g, "").replace(".html", "");
  const shot = `visual-polish-${slug}-${vpName}.png`;
  await page.screenshot({ path: `${ART}/${shot}`, fullPage: false });
  return { vpName, shot, metrics, path: spec.path };
}

async function main() {
  const browser = await chromium.launch();
  const results = [];
  const viewports = [
    ["375", 375, 812],
    ["400", 400, 820],
    ["1280", 1280, 800],
  ];
  for (const spec of PAGES) {
    const page = await browser.newPage();
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        page.evaluate((t) => {
          window.__qaConsoleErrors = window.__qaConsoleErrors || [];
          window.__qaConsoleErrors.push(t);
        }, msg.text()).catch(() => {});
      }
    });
    page.on("pageerror", (err) => {
      page.evaluate((t) => {
        window.__qaConsoleErrors = window.__qaConsoleErrors || [];
        window.__qaConsoleErrors.push(t);
      }, String(err)).catch(() => {});
    });
    for (const [name, w, h] of viewports) {
      results.push(await auditPage(page, spec, name, w, h));
    }
    await page.close();
  }
  await browser.close();

  const pass = results.every((r) => {
    const m = r.metrics;
    return (
      m.motionOn &&
      m.pageReady &&
      m.loadState === "ready" &&
      !m.docOverflow &&
      m.chartsReady &&
      m.chartCount >= 1 &&
      m.consoleErrors.length === 0
    );
  });
  const report = { pass, base, results };
  writeFileSync(`${ART}/visual-polish-qa.json`, JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  if (!pass) process.exit(1);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
