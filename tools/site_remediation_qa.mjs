#!/usr/bin/env node
/**
 * Site remediation QA — hub overflow + case-study caption gaps.
 */
import { chromium, webkit } from "playwright";
import { mkdirSync, writeFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const base = (process.argv[2] || "http://127.0.0.1:8765").replace(/\/$/, "");
const ART = process.env.SITE_QA_ARTIFACT_DIR || "/opt/cursor/artifacts";
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

const PAGES = [
  { path: "/index.html", id: "hub" },
  { path: "/case-studies.html", id: "case-studies" },
  { path: "/demo.html", id: "demo" },
];

const VIEWPORTS = [
  ["375", 375, 812, 1],
  ["390", 390, 844, 1],
  ["400", 400, 820, 1],
  ["1280", 1280, 800, 1],
  ["375-zoom200", 375, 812, 2],
];

async function auditHub(page) {
  return page.evaluate(() => {
    const doc = document.documentElement;
    const hero = document.querySelector(".hero h1");
    const heroRect = hero?.getBoundingClientRect();
    const docW = doc.clientWidth;
    return {
      docScroll: doc.scrollWidth,
      docClient: doc.clientWidth,
      heroOverflowsViewport: heroRect ? heroRect.right > docW + 4 : false,
      heroRight: heroRect?.right,
      docW,
    };
  });
}

async function auditPage(page, spec, vpName) {
  await page.goto(`${base}${spec.path}`, { waitUntil: "networkidle", timeout: 45_000 });
  if (spec.path.includes("case-studies")) {
    await page.waitForFunction(
      () => document.getElementById("ni-chart-caption")?.textContent?.includes("prescription"),
      { timeout: 20_000 },
    );
  } else if (spec.path.includes("index")) {
    await page.waitForFunction(
      () => document.getElementById("takeaway-cpih")?.textContent?.length > 10,
      { timeout: 20_000 },
    );
  }
  const hub = await auditHub(page);
  let captions = null;
  if (spec.path.includes("case-studies")) {
    captions = await page.evaluate(() =>
      ["study-ni", "study-trade"].map((id) => {
        const study = document.getElementById(id);
        const canvas = study?.querySelector("canvas");
        const caption = study?.querySelector(".cs-chart-caption");
        const chart = canvas ? window.Chart?.getChart(canvas) : null;
        const canvasRect = canvas?.getBoundingClientRect();
        const capRect = caption?.getBoundingClientRect();
        const chartArea = chart?.chartArea;
        let xLabelBottom = canvasRect?.bottom ?? 0;
        if (chartArea && canvasRect) {
          xLabelBottom = canvasRect.top + (chartArea.bottom - chartArea.top);
        }
        const gapPx = (capRect?.top ?? 0) - xLabelBottom;
        const plugins = chart?.config?.plugins ?? [];
        return {
          id,
          gapPx,
          ok: gapPx >= 6 && !plugins.some((p) => typeof p?.afterDraw === "function"),
        };
      }),
    );
  }
  mkdirSync(ART, { recursive: true });
  const shot = `site-remediation-${spec.id}-${vpName}.png`;
  await page.screenshot({ path: `${ART}/${shot}`, fullPage: false });
  return { vpName, shot, hub, captions, path: spec.path };
}

async function runEngine(label) {
  const browser = await (label === "webkit" ? webkit : chromium).launch();
  const results = [];
  for (const spec of PAGES) {
    for (const [name, w, h, scale] of VIEWPORTS) {
      const ctx = await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: scale });
      const page = await ctx.newPage();
      const vpKey = label === "chromium" ? name : `${name}-${label}`;
      results.push(await auditPage(page, spec, vpKey));
      await ctx.close();
    }
  }
  await browser.close();
  return results;
}

async function main() {
  const cs = spawnSync("node", [path.join(ROOT, "tools/case_studies_layout_qa.mjs"), base], {
    env: { ...process.env, CASE_STUDIES_QA_ARTIFACT_DIR: ART },
    encoding: "utf8",
  });
  if (cs.status !== 0) {
    console.error(cs.stderr || cs.stdout);
    process.exit(1);
  }
  const chromiumResults = await runEngine("chromium");
  let webkitResults = [];
  try {
    webkitResults = await runEngine("webkit");
  } catch (e) {
    webkitResults = [{ error: String(e) }];
  }
  const pass = chromiumResults.every((r) => {
    const slack = r.hub.docScroll - r.hub.docClient;
    return (
      slack <= 8 &&
      !r.hub.heroOverflowsViewport &&
      (!r.captions || r.captions.every((c) => c.ok))
    );
  });
  const report = { pass, base, chromiumResults, webkitResults };
  writeFileSync(`${ART}/site-remediation-qa.json`, JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  if (!pass) process.exit(1);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
