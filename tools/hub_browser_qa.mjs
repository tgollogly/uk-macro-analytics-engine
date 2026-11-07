/**
 * Headless smoke + a11y spot-checks for uk-macro-analytics-landing preview.
 * Usage: node tools/hub_browser_qa.mjs [baseUrl]
 * Writes JSON report + PNG screenshots under ARTIFACT_DIR (default /opt/cursor/artifacts).
 */
import { chromium, devices, webkit } from "playwright";
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
  contrast: [],
  notes: [
    "Chromium desktop + 375 (iPhone 13 UA); optional WebKit mobile400 if installed.",
    "Every route: rendered text contrast on key controls (AA 4.5:1 normal, 3:1 large/bold).",
    "Macro explorer: Chart.js legend/tick colours after render; mobile toolbar screenshot.",
    "Heat/Thermal: contrast on static chrome only — weather tiles may stay empty without live API.",
    "Not WCAG / axe certification.",
  ],
};

const ROUTE_CONTRAST_PROBES = {
  hub: ["h1", ".takeaway", ".story-q", ".hub-card p"],
  "macro-charts": [".kpi", ".demo-card h2", "#cpih-h2", "#psnb-h2"],
  "macro-explorer": ["#series", "#from", "#to", "#window", "#view-summary", "table.data td"],
  "data-coverage": [".head p", "table.cov td", "table.cov th"],
  beneish: ["input", "table td", "button"],
  "heat-dome": ["#q", ".head h1", ".hint"],
  "thermal-compare": ["#q", ".head h1"],
  bundlebuilder: ["#dTitle", "textarea#dDesc", ".btn-p"],
  "ats-retired": [".head h1", ".head p"],
  privacy: [".doc p", ".doc h1"],
};

async function auditRouteContrast(page, routeName, vpLabel) {
  const probes = ROUTE_CONTRAST_PROBES[routeName];
  if (!probes?.length) return [];
  const results = await page.evaluate((probeList) => {
    function parseCssRgb(css) {
      if (!css || css === "transparent") return null;
      const m = css.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
      if (m) return [Number(m[1]), Number(m[2]), Number(m[3])];
      return null;
    }
    function lin(c) {
      const x = c / 255;
      return x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4;
    }
    function relLuminance([r, g, b]) {
      return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
    }
    function contrastRatio(fgRgb, bgRgb) {
      const l1 = relLuminance(fgRgb);
      const l2 = relLuminance(bgRgb);
      const hi = Math.max(l1, l2);
      const lo = Math.min(l1, l2);
      return (hi + 0.05) / (lo + 0.05);
    }
    function effectiveBackgroundRgb(node) {
      let el = node;
      while (el && el !== document.documentElement) {
        const cs = getComputedStyle(el);
        const rgb = parseCssRgb(cs.backgroundColor);
        if (rgb && cs.backgroundColor !== "rgba(0, 0, 0, 0)") return rgb;
        el = el.parentElement;
      }
      return parseCssRgb(getComputedStyle(document.body).backgroundColor) || [250, 248, 244];
    }
    function measure(selector) {
      const el = document.querySelector(selector);
      if (!el) return { ok: false, reason: "missing", selector };
      const cs = getComputedStyle(el);
      const fg = parseCssRgb(cs.color);
      const wk = parseCssRgb(cs.webkitTextFillColor);
      const fill =
        wk && cs.webkitTextFillColor !== "rgba(0, 0, 0, 0)" && cs.webkitTextFillColor !== "rgb(0, 0, 0)"
          ? wk
          : fg;
      const bg = effectiveBackgroundRgb(el);
      if (!fill || !bg) {
        return { ok: false, reason: "unparsed", selector, color: cs.color, webkit: cs.webkitTextFillColor };
      }
      const ratio = contrastRatio(fill, bg);
      const px = parseFloat(cs.fontSize) || 16;
      const bold = cs.fontWeight === "bold" || Number(cs.fontWeight) >= 600;
      const large = px >= 18 || (px >= 14 && bold);
      const min = large ? 3 : 4.5;
      return {
        ok: ratio >= min,
        ratio,
        min,
        large,
        selector,
        color: cs.color,
        webkitTextFill: cs.webkitTextFillColor,
        fontSize: cs.fontSize,
      };
    }
    return probeList.map(measure);
  }, probes);
  for (const r of results) {
    report.contrast.push({ route: routeName, viewport: vpLabel, ...r });
    if (r.reason === "missing") continue;
    if (!r.ok) {
      const msg = r.reason
        ? `${r.selector}: ${r.reason}`
        : `${r.selector} ${r.ratio?.toFixed(2)}:1 < ${r.min}:1 (${r.color}${r.webkitTextFill ? ` webkit=${r.webkitTextFill}` : ""})`;
      pushError(`contrast:${routeName}:${vpLabel}`, msg);
    }
  }
  return results;
}

async function auditMacroChartTheme(page, canvasId, routeName, vpLabel) {
  const info = await page.evaluate((id) => {
    const canvas = document.getElementById(id);
    const chart = typeof Chart !== "undefined" && canvas ? Chart.getChart(canvas) : null;
    if (!chart?.options) return { ok: false, reason: "no chart instance" };
    const leg = chart.options.plugins?.legend?.labels?.color;
    const xT = chart.options.scales?.x?.ticks?.color;
    const yT = chart.options.scales?.y?.ticks?.color;
    const bad = [];
    if (String(leg).toLowerCase() === "#e2e8f0") bad.push("legend #e2e8f0");
    if (String(xT).toLowerCase() === "#94a3b8") bad.push("x tick #94a3b8");
    if (String(yT).toLowerCase() === "#94a3b8") bad.push("y tick #94a3b8");
    return { ok: bad.length === 0, bad, leg, xT, yT, canvasId: id };
  }, canvasId);
  report.contrast.push({ route: routeName, viewport: vpLabel, chartTheme: info });
  if (!info.ok) {
    pushError(
      `chart-theme:${routeName}:${vpLabel}`,
      info.reason || info.bad?.join(", ") || "chart theme failed",
    );
  }
  return info;
}

/** Map pages (MapLibre) and print PDF can poison the next route in one context — audit in fresh pages. */
const ISOLATED_CONTRAST_ROUTES = new Set(["ats-retired"]);

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
    ...(vp.label === "mobile375" && devices["iPhone 13"]?.userAgent
      ? { userAgent: devices["iPhone 13"].userAgent }
      : {}),
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
  await page
    .waitForFunction(
      () => {
        const t = document.getElementById("takeaway-cpih")?.textContent || "";
        return t.length > 16 && !/Loading/i.test(t);
      },
      { timeout: 20000 },
    )
    .catch(() => {});
  vpOut.routes.hub = await checkHub(page, vp);
  await auditRouteContrast(page, "hub", vp.label);

  for (const { name, path } of ROUTES.slice(1)) {
    const url = `${report.base}${path}`;
    const resp = await page.goto(url, { waitUntil: "domcontentloaded" });
    const status = resp?.status();
    if (status && status >= 400) pushError(name, `HTTP ${status} for ${path}`);

    if (name === "macro-explorer") {
      await page.waitForSelector("#view-summary", { timeout: 20000 });
      await page.waitForFunction(
        () => {
          const t = document.getElementById("view-summary")?.textContent || "";
          return t.length > 40 && !/Loading|Adjust filters/.test(t);
        },
        { timeout: 20000 },
      );
      await auditMacroChartTheme(page, "chart", name, vp.label);
      if (vp.label === "desktop") {
        vpOut.routes[name] = await checkMacroExplorer(page);
      }
    } else if (name === "macro-charts") {
      await page.waitForSelector("#chart-cpih", { timeout: 20000 });
      await page.waitForFunction(() => typeof Chart !== "undefined" && Chart.getChart("chart-cpih"), {
        timeout: 20000,
      });
      await auditMacroChartTheme(page, "chart-cpih", name, vp.label);
      await auditMacroChartTheme(page, "chart-psnb", name, vp.label);
    } else if (name === "bundlebuilder" && vp.label === "desktop") {
      vpOut.routes[name] = await checkBundlePdf(page);
      await page.emulateMedia({ media: "screen", colorScheme: "light" });
      // Reset print emulation bleed (Chromium retains computed colours on next origin navigation).
      await page.goto("about:blank");
    } else if (name === "ats-retired") {
      await checkAtsRetired(page);
    }

    await page.emulateMedia({ media: "screen", colorScheme: "light" });
    if (!ISOLATED_CONTRAST_ROUTES.has(name)) {
      await auditRouteContrast(page, name, vp.label);
    }

    if (vp.label === "mobile375" || name === "privacy") {
      await spotA11y(page, name);
    }
    if (vp.label === "mobile375" && (name === "hub" || name === "macro-explorer")) {
      const shotName =
        name === "macro-explorer" ? `macro-explorer-controls-${vp.label}` : `${name}-${vp.label}`;
      await page.screenshot({
        path: join(ARTIFACT_DIR, `${shotName}.png`),
        fullPage: name === "hub",
      });
      if (name === "macro-explorer") {
        await page.locator(".toolbar").screenshot({
          path: join(ARTIFACT_DIR, `macro-explorer-toolbar-${vp.label}.png`),
        });
      }
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

async function auditIsolatedRouteContrasts() {
  for (const vp of VIEWPORTS) {
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
      viewport: { width: vp.width, height: vp.height },
      ...(vp.label === "mobile375" && devices["iPhone 13"]?.userAgent
        ? { userAgent: devices["iPhone 13"].userAgent }
        : {}),
    });
    const page = await context.newPage();
    for (const routeName of ISOLATED_CONTRAST_ROUTES) {
      const path = ROUTES.find((r) => r.name === routeName)?.path;
      if (!path) continue;
      await page.goto(`${report.base}${path}`, { waitUntil: "networkidle" });
      await page
        .waitForFunction(
          () => {
            const ink = getComputedStyle(document.documentElement).getPropertyValue("--ink").trim();
            const body = getComputedStyle(document.body).color;
            return ink.length > 3 && body !== "rgb(0, 0, 0)";
          },
          { timeout: 15000 },
        )
        .catch(async () => {
          await page.reload({ waitUntil: "networkidle" });
        });
      await auditRouteContrast(page, routeName, vp.label);
    }
    await browser.close();
  }
  report.notes.push("ats-retired contrast audited in isolated browser contexts (post map/print tours)");
}

await auditIsolatedRouteContrasts();

// Optional WebKit pass (closer to iPhone Safari than Chromium — requires playwright webkit).
try {
  const wb = await webkit.launch({ headless: true });
  const ctx = await wb.newContext({
    viewport: { width: 400, height: 844 },
    deviceScaleFactor: 2,
    isMobile: true,
    hasTouch: true,
    reducedMotion: "reduce",
  });
  const page = await ctx.newPage();
  await page.goto(`${report.base}/portfolio/macro-explorer.html`, { waitUntil: "networkidle" });
  await page.waitForSelector("#view-summary", { timeout: 25000 });
  await auditRouteContrast(page, "macro-explorer", "webkit400");
  await auditMacroChartTheme(page, "chart", "macro-explorer", "webkit400");
  await page.locator(".toolbar").screenshot({
    path: join(ARTIFACT_DIR, "macro-explorer-toolbar-webkit400.png"),
  });
  await wb.close();
  report.notes.push("webkit400 macro-explorer contrast pass completed");
} catch (e) {
  report.notes.push(`webkit400 skipped: ${String(e).slice(0, 120)}`);
}

async function auditMotionEnabled(base) {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto(`${base}/portfolio/macro-explorer.html`, { waitUntil: "networkidle" });
  await page.waitForFunction(
    () => {
      const t = document.getElementById("view-summary")?.textContent || "";
      return t.length > 40 && !/Loading|Adjust filters/.test(t);
    },
    { timeout: 20000 },
  );
  const before = await page.evaluate(() => Chart.getChart("chart")?.options?.animation?.duration);
  await page.locator("#window").selectOption("24");
  await page.locator("#apply").click();
  await page.waitForTimeout(500);
  const motion = await page.evaluate(() => ({
    reduced: matchMedia("(prefers-reduced-motion: reduce)").matches,
    duration: Chart.getChart("chart")?.options?.animation?.duration,
    viewTransitionMeta: !!document.querySelector('meta[name="view-transition"]'),
    hubMotionCss: [...document.styleSheets].some((s) => String(s.href || "").includes("hub-motion")),
  }));
  report.contrast.push({ route: "macro-explorer", viewport: "motion-default", motion });
  if (!motion.reduced && (!motion.duration || motion.duration < 100)) {
    pushError("motion", `expected chart animation duration, got ${motion.duration}`);
  }
  await browser.close();
}

async function auditMotionReduced(base) {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ reducedMotion: "reduce" });
  const page = await context.newPage();
  await page.goto(`${base}/portfolio/macro-explorer.html`, { waitUntil: "networkidle" });
  await page.waitForFunction(() => typeof Chart !== "undefined" && Chart.getChart("chart"), {
    timeout: 20000,
  });
  const motion = await page.evaluate(() => ({
    reduced: matchMedia("(prefers-reduced-motion: reduce)").matches,
    duration: Chart.getChart("chart")?.options?.animation?.duration,
  }));
  report.contrast.push({ route: "macro-explorer", viewport: "motion-reduce", motion });
  if (motion.duration !== 0) {
    pushError("motion-reduce", `expected duration 0, got ${motion.duration}`);
  }
  await browser.close();
}

await auditMotionEnabled(report.base);
await auditMotionReduced(report.base);

report.pass = report.errors.length === 0;
writeFileSync(join(ARTIFACT_DIR, "hub-browser-qa-report.json"), JSON.stringify(report, null, 2));
console.log(JSON.stringify({ pass: report.pass, errors: report.errors }, null, 2));
process.exit(report.pass ? 0 : 1);
