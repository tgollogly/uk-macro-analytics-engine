/**
 * Headless smoke + a11y spot-checks for uk-macro-analytics-landing preview.
 * Usage: node tools/hub_browser_qa.mjs [baseUrl]
 * Writes JSON report + PNG screenshots under ARTIFACT_DIR (default /opt/cursor/artifacts).
 */
import { chromium, devices } from "playwright";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const BASE =
  process.argv[2] || "https://uk-macro-analytics-landing.thomasgolloglypagesdev.workers.dev";
const ARTIFACT_DIR = process.env.HUB_QA_ARTIFACT_DIR || "/opt/cursor/artifacts";
const report = {
  base: BASE.replace(/\/$/, ""),
  viewports: {},
  routes: [],
  errors: [],
  notes: [
    "Headless Chromium in agent VM — not parent Chrome at 400px.",
    "375px: hub card count + optional horizontal overflow check + hub screenshot only (not all 10 routes).",
    "Desktop: full route load; deep macro + bundle PDF only on 1280 viewport.",
    "a11y: privacy route + mobile pass get minimal spot checks (h1, skip); not WCAG / axe.",
    "Browser context sets prefers-reduced-motion: reduce; no keyboard tab-order audit.",
  ],
};

const ROUTES = [
  { name: "hub", path: "/" },
  { name: "macro-charts", path: "/demo.html" },
  { name: "macro-explorer", path: "/portfolio/macro-explorer.html" },
  { name: "data-coverage", path: "/portfolio/data-coverage.html" },
  { name: "beneish", path: "/portfolio/beneish.html" },
  { name: "heat-dome", path: "/portfolio/heat-dome.html" },
  { name: "thermal-compare", path: "/portfolio/thermal-compare.html" },
  { name: "bundlebuilder", path: "/portfolio/bundlebuilder.html" },
  { name: "ats-retired", path: "/portfolio/ats-matcher.html" },
  { name: "privacy", path: "/portfolio/privacy.html" },
];

const VIEWPORTS = [
  { label: "desktop", width: 1280, height: 800 },
  { label: "mobile375", width: 375, height: 812 },
];

mkdirSync(ARTIFACT_DIR, { recursive: true });

function pushError(where, message) {
  report.errors.push({ where, message });
}

async function checkHub(page, vp) {
  const demoCards = await page.locator(
    'main a.btn-primary[href="./demo.html"], main a.btn-primary[href*="portfolio/"]',
  ).count();
  const retired = await page.getByText(/ATS.*retired/i).count();
  const demosNav = await page.getByRole("link", { name: "Demos" }).count();
  if (demoCards < 7) pushError("hub", `expected 7 demo primary links, got ${demoCards}`);
  if (demosNav < 1) pushError("hub", "missing Demos nav link");
  if (retired < 1) pushError("hub", "missing retired ATS copy on hub");
  await page.screenshot({ path: join(ARTIFACT_DIR, `hub-${vp.label}.png`), fullPage: true });
  let overflow = null;
  if (vp.label === "mobile375") {
    overflow = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      innerWidth: window.innerWidth,
    }));
    if (overflow.scrollWidth > overflow.innerWidth + 2) {
      pushError(
        "hub-375-overflow",
        `horizontal overflow scrollWidth=${overflow.scrollWidth} inner=${overflow.innerWidth}`,
      );
    }
  }
  return { demoCards, retired, demosNav, overflow };
}

async function checkMacroExplorer(page) {
  await page.waitForSelector("#view-summary", { timeout: 20000 });
  await page.waitForFunction(
    () => {
      const t = document.getElementById("view-summary")?.textContent || "";
      return t.length > 40 && !/Loading|Adjust filters/.test(t);
    },
    { timeout: 20000 },
  );
  const summary = await page.locator("#view-summary").textContent();
  const rows = await page.locator("#tbl tbody tr").count();
  if (!/capped at 24|all \d+ month/i.test(summary || "")) {
    pushError("macro-explorer", `unexpected summary: ${summary?.slice(0, 120)}`);
  }
  await page.locator("#window").selectOption("24");
  await page.locator("#apply").click();
  await page.waitForTimeout(400);
  const summary24 = await page.locator("#view-summary").textContent();
  const rows24 = await page.locator("#tbl tbody tr").count();
  if (rows24 > 24) pushError("macro-explorer", `table shows ${rows24} rows after 24-mo window`);
  // Manual 6-month narrow range
  await page.locator("#window").selectOption("all");
  await page.locator("#from").fill("2026-04");
  await page.locator("#to").fill("2026-09");
  await page.locator("#apply").click();
  await page.waitForTimeout(400);
  const summary6 = await page.locator("#view-summary").textContent();
  const rows6 = await page.locator("#tbl tbody tr").count();
  if (rows6 !== 6 || !/all 6 month/i.test(summary6 || "")) {
    pushError(
      "macro-explorer-6mo",
      `6mo range: rows=${rows6} summary=${summary6?.slice(0, 120)}`,
    );
  }
  const [download] = await Promise.all([
    page.waitForEvent("download", { timeout: 10000 }),
    page.locator("#csv").click(),
  ]);
  const csvPath = await download.path();
  const { readFileSync } = await import("node:fs");
  const csv = readFileSync(csvPath, "utf8");
  const csvLines = csv.trim().split("\n").length - 1;
  if (csvLines !== 6) pushError("macro-explorer-csv", `expected 6 CSV data rows, got ${csvLines}`);
  await page.screenshot({ path: join(ARTIFACT_DIR, "macro-explorer-desktop.png") });
  return { summary, rows, summary24, rows24, summary6, rows6, csvLines };
}

async function checkAtsRetired(page) {
  const body = await page.content();
  if (/config\.js|fetch\(/.test(body) && !/no.*config\.js/i.test(body)) {
    pushError("ats", "unexpected active fetch/config patterns");
  }
  if ((await page.getByText(/retired/i).count()) < 1) pushError("ats", "missing retired wording");
}

async function checkBundlePdf(page) {
  await page.getByRole("button", { name: /Load sample/i }).click();
  await page.waitForTimeout(300);
  const printHtml = await page.locator("#printArea").innerHTML();
  if (!/Sample contract|fictional/i.test(printHtml)) {
    pushError("bundlebuilder", "printArea missing sample fictional exhibits");
  }
  await page.emulateMedia({ media: "print" });
  const pdfPath = join(ARTIFACT_DIR, "bundlebuilder-sample.pdf");
  await page.pdf({ path: pdfPath, printBackground: true, format: "A4" });
  const { readFileSync, statSync } = await import("node:fs");
  const head = readFileSync(pdfPath).subarray(0, 5).toString("utf8");
  if (head !== "%PDF-") pushError("bundlebuilder", `invalid PDF header: ${head}`);
  if (statSync(pdfPath).size < 800) pushError("bundlebuilder", "PDF suspiciously small");
  await page.emulateMedia({ media: "screen" });
  return { pdfBytes: statSync(pdfPath).size, printLen: printHtml.length };
}

async function spotA11y(page, routeName) {
  const reduced = await page.emulateMedia({ media: "screen", reducedMotion: "reduce" });
  void reduced;
  const main = page.locator("main, [role='main'], body");
  await main.first().focus().catch(() => {});
  const skip = await page.locator(".skip, a.skip").count();
  const h1 = await page.locator("h1").count();
  if (h1 < 1 && routeName !== "hub") pushError(`a11y:${routeName}`, "missing h1");
  const unlabeledSelect = await page
    .locator("select:not([aria-label]):not([id])")
    .count();
  if (unlabeledSelect > 0) pushError(`a11y:${routeName}`, `${unlabeledSelect} bare selects`);
}

async function runViewport(vp) {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: vp.width, height: vp.height },
    reducedMotion: "reduce",
    userAgent: devices["iPhone 13"]?.userAgent,
  });
  context.setDefaultTimeout(25000);
  const page = await context.newPage();
  const consoleErrors = [];
  page.on("pageerror", (e) => consoleErrors.push(String(e)));
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });

  const vpOut = { routes: {}, consoleErrors: [] };

  await page.goto(`${report.base}/`, { waitUntil: "networkidle" });
  vpOut.routes.hub = await checkHub(page, vp);

  for (const { name, path } of ROUTES.slice(1)) {
    const url = `${report.base}${path}`;
    const resp = await page.goto(url, { waitUntil: "domcontentloaded" });
    const status = resp?.status();
    if (status && status >= 400) pushError(name, `HTTP ${status} for ${path}`);
    if (name === "macro-explorer" && vp.label === "desktop") {
      vpOut.routes[name] = await checkMacroExplorer(page);
    } else if (name === "bundlebuilder" && vp.label === "desktop") {
      vpOut.routes[name] = await checkBundlePdf(page);
    } else if (name === "ats-retired") {
      await checkAtsRetired(page);
    }
    if (vp.label === "mobile375" || name === "privacy") {
      await spotA11y(page, name);
    }
    if (vp.label === "mobile375" && (name === "hub" || name === "macro-explorer")) {
      await page.screenshot({
        path: join(ARTIFACT_DIR, `${name}-${vp.label}.png`),
        fullPage: name === "hub",
      });
    }
  }

  const favicon = await page.request.get(`${report.base}/favicon.ico`);
  if (favicon.status() !== 200) pushError("favicon", `favicon HTTP ${favicon.status()}`);

  vpOut.consoleErrors = consoleErrors.filter(
    (t) => !/favicon\.ico.*404/i.test(t) && !/Failed to load resource.*favicon/i.test(t),
  );
  if (vpOut.consoleErrors.length) {
    pushError(`console:${vp.label}`, vpOut.consoleErrors.join(" | ").slice(0, 500));
  }

  await browser.close();
  report.viewports[vp.label] = vpOut;
}

for (const vp of VIEWPORTS) {
  await runViewport(vp);
}

report.pass = report.errors.length === 0;
writeFileSync(join(ARTIFACT_DIR, "hub-browser-qa-report.json"), JSON.stringify(report, null, 2));
console.log(JSON.stringify({ pass: report.pass, errors: report.errors }, null, 2));
process.exit(report.pass ? 0 : 1);
