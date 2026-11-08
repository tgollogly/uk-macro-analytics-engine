#!/usr/bin/env node
/**
 * Case studies layout QA — overflow, caption vs x-axis separation, no canvas KPI plugins.
 * Usage: node tools/case_studies_layout_qa.mjs <baseUrl>
 */
import { chromium, webkit } from "playwright";
import { mkdirSync, writeFileSync } from "node:fs";

const base = (process.argv[2] || "http://127.0.0.1:8765").replace(/\/$/, "");
const ART = process.env.CASE_STUDIES_QA_ARTIFACT_DIR || "/opt/cursor/artifacts";

const VIEWPORTS = [
  ["375", 375, 812, 1],
  ["390", 390, 844, 1],
  ["400", 400, 820, 1],
  ["1280", 1280, 800, 1],
  ["375-zoom200", 375, 812, 2],
];

async function audit(page, vpName) {
  await page.goto(`${base}/case-studies.html`, { waitUntil: "networkidle", timeout: 45_000 });
  await page.waitForFunction(
    () => {
      const ni = document.getElementById("ni-chart-caption");
      const tr = document.getElementById("trade-chart-caption");
      return Boolean(ni?.textContent?.includes("prescription items") && tr?.textContent?.includes("YoY"));
    },
    { timeout: 20_000 },
  );
  await page.waitForTimeout(400);

  const metrics = await page.evaluate(() => {
    const doc = document.documentElement;
    const studyIds = ["study-ni", "study-trade"];
    const charts = studyIds.map((id) => {
      const study = document.getElementById(id);
      const canvas = study?.querySelector("canvas");
      const caption = study?.querySelector(".cs-chart-caption");
      const chart = canvas ? window.Chart?.getChart(canvas) : null;
      const canvasRect = canvas?.getBoundingClientRect();
      const capRect = caption?.getBoundingClientRect();
      const chartArea = chart?.chartArea;
      let xLabelBottom = chartArea?.bottom ?? canvasRect?.bottom ?? 0;
      if (chartArea && canvasRect) {
        xLabelBottom = canvasRect.top + (chartArea.bottom - chartArea.top);
      }
      const capTop = capRect?.top ?? 0;
      const gapPx = capTop - xLabelBottom;
      const plugins = chart?.config?.plugins ?? [];
      const hasAfterDrawKpi = plugins.some((p) => typeof p?.afterDraw === "function");
      return {
        id,
        gapPx,
        captionBelowAxis: gapPx >= 8,
        captionOverlapsAxis: gapPx < 4,
        hasAfterDrawKpi,
        captionText: caption?.textContent?.slice(0, 80) ?? "",
        canvasPluginCount: plugins.length,
      };
    });

    const cards = [...document.querySelectorAll(".cs-study")];
    return {
      docOverflow: doc.scrollWidth > doc.clientWidth + 1,
      docScroll: doc.scrollWidth,
      docClient: doc.clientWidth,
      charts,
      cards: cards.map((el) => ({
        id: el.id,
        overflow: el.scrollWidth > el.clientWidth + 1,
      })),
    };
  });

  mkdirSync(ART, { recursive: true });
  const shot = `case-studies-caption-qa-${vpName}.png`;
  await page.screenshot({ path: `${ART}/${shot}`, fullPage: false });
  return { vpName, shot, metrics };
}

function passResult(r) {
  const m = r.metrics;
  const docSlack = m.docScroll - m.docClient;
  if (docSlack > 12) return false;
  if (!m.cards.every((c) => !c.overflow)) return false;
  return m.charts.every(
    (c) => c.captionBelowAxis && !c.captionOverlapsAxis && !c.hasAfterDrawKpi,
  );
}

async function runBrowser(label) {
  const browser = await (label === "webkit" ? webkit : chromium).launch();
  const results = [];
  for (const [name, w, h, scale] of VIEWPORTS) {
    const vpKey = label === "chromium" ? name : `${name}-${label}`;
    const context = await browser.newContext({
      viewport: { width: w, height: h },
      deviceScaleFactor: scale,
    });
    const page = await context.newPage();
    results.push(await audit(page, vpKey));
    await context.close();
  }
  await browser.close();
  return results;
}

async function main() {
  const chromiumResults = await runBrowser("chromium");
  let webkitResults = [];
  try {
    webkitResults = await runBrowser("webkit");
  } catch (e) {
    webkitResults = [{ vpName: "webkit-skipped", error: String(e), metrics: null }];
  }

  const results = [...chromiumResults, ...webkitResults.filter((r) => r.metrics)];
  const pass = results.every((r) => r.metrics && passResult(r));
  const report = { pass, base, results };
  writeFileSync(`${ART}/case-studies-caption-qa.json`, JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  if (!pass) process.exit(1);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
