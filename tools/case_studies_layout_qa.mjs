#!/usr/bin/env node
/**
 * Case studies responsive overflow QA — scrollWidth vs clientWidth per card.
 * Usage: node tools/case_studies_layout_qa.mjs <baseUrl>
 */
import { chromium } from "playwright";
import { mkdirSync, writeFileSync } from "node:fs";

const base = (process.argv[2] || "http://127.0.0.1:8765").replace(/\/$/, "");
const ART = process.env.CASE_STUDIES_QA_ARTIFACT_DIR || "/opt/cursor/artifacts";

async function checkViewport(page, name) {
  await page.goto(`${base}/case-studies.html`, { waitUntil: "networkidle", timeout: 30_000 });
  await page.waitForSelector("#ni-findings:not(:has-text('Loading'))", { timeout: 10_000 }).catch(() => {});
  await page.waitForTimeout(600);
  const metrics = await page.evaluate(() => {
    const doc = document.documentElement;
    const body = document.body;
    const cards = [...document.querySelectorAll(".cs-study")];
    return {
      docScroll: doc.scrollWidth,
      docClient: doc.clientWidth,
      bodyScroll: body.scrollWidth,
      bodyClient: body.clientWidth,
      docOverflow: doc.scrollWidth > doc.clientWidth + 1,
      cards: cards.map((el, i) => ({
        id: el.id || `card-${i}`,
        scrollWidth: el.scrollWidth,
        clientWidth: el.clientWidth,
        overflow: el.scrollWidth > el.clientWidth + 1,
      })),
    };
  });
  mkdirSync(ART, { recursive: true });
  await page.screenshot({ path: `${ART}/case-studies-qa-${name}.png`, fullPage: true });
  return { name, metrics };
}

async function main() {
  const browser = await chromium.launch();
  const results = [];
  for (const [name, w, h] of [
    ["375", 375, 812],
    ["400", 400, 820],
  ]) {
    const page = await browser.newPage({ viewport: { width: w, height: h } });
    results.push(await checkViewport(page, name));
    await page.close();
  }
  await browser.close();
  const pass = results.every(
    (r) => !r.metrics.docOverflow && r.metrics.cards.every((c) => !c.overflow),
  );
  const report = { pass, results, base };
  writeFileSync(`${ART}/case-studies-layout-qa.json`, JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  if (!pass) process.exit(1);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
