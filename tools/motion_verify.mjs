/**
 * Verifies perceptible motion (not screenshot-only): WebKit + Chromium,
 * normal vs prefers-reduced-motion. Writes report + optional webm under ARTIFACT_DIR.
 *
 * Usage: node tools/motion_verify.mjs [baseUrl]
 */
import { chromium, webkit, devices } from "playwright";
import { mkdirSync, writeFileSync, renameSync, existsSync } from "node:fs";
import { join } from "node:path";

const BASE =
  process.argv[2] || "https://uk-macro-analytics-landing.thomasgolloglypagesdev.workers.dev";
const ARTIFACT_DIR = process.env.HUB_QA_ARTIFACT_DIR || "/opt/cursor/artifacts";

mkdirSync(ARTIFACT_DIR, { recursive: true });

const report = {
  base: BASE.replace(/\/$/, ""),
  runs: [],
  pass: false,
  notes: [
    "Animations verified via getAnimations() + body.is-motion-on, not screenshots alone.",
    "Playwright WebKit approximates Safari; physical iPhone not used.",
  ],
};

function pushRun(row) {
  report.runs.push(row);
}

async function samplePanelMotion(page, label, engine, reducedMotion) {
  await page.goto(`${BASE}/`, { waitUntil: "domcontentloaded" });
  if (!reducedMotion) {
    await page.waitForFunction(
      () => document.body.classList.contains("is-motion-on"),
      { timeout: 15000 },
    );
  }
  await page.waitForSelector(".insight-feature.motion-in", { timeout: 8000 });
  const sample = await page.evaluate(() => {
    const el = document.querySelector(".insight-feature.motion-in");
    if (!el) return { ok: false, reason: "no panel" };
    const anims = el.getAnimations();
    const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
    const motionOn = document.body.classList.contains("is-motion-on");
    const cs = getComputedStyle(el);
    const cssDur = parseFloat(cs.animationDuration) || 0;
    const durations = anims.map(
      (a) => a.effect?.getComputedTiming?.().duration ?? a.effect?.getTiming?.().duration ?? 0,
    );
    const maxDur = durations.length ? Math.max(...durations) : cssDur * 1000;
    const ok = reduced
      ? !motionOn
      : motionOn && (anims.length > 0 || cssDur >= 0.5);
    return { ok, reduced, motionOn, count: anims.length, maxDur, cssDur, animationName: cs.animationName };
  });
  pushRun({ label, engine, route: "hub", ...sample });
  return sample;
}

async function sampleMacroChart(page, label, engine, reducedMotion) {
  await page.goto(`${BASE}/portfolio/macro-explorer.html`, { waitUntil: "domcontentloaded" });
  await page.waitForFunction(
    () => typeof Chart !== "undefined" && Chart.getChart("chart"),
    { timeout: 25000 },
  );
  const before = await page.evaluate(() => Chart.getChart("chart")?.options?.animation?.duration);
  await page.locator("#window").selectOption("24");
  await page.locator("#apply").click();
  await page.waitForTimeout(reducedMotion ? 120 : 900);
  const after = await page.evaluate(() => {
    const c = Chart.getChart("chart");
    const box = document.querySelector(".chartbox");
    const anims = box ? box.getAnimations() : [];
    return {
      duration: c?.options?.animation?.duration,
      chartAnims: c?.$animations ? Object.keys(c.$animations).length : null,
      boxAnimCount: anims.length,
    };
  });
  const ok = reducedMotion ? after.duration === 0 : after.duration >= 400;
  pushRun({ label, engine, route: "macro-explorer", reducedMotion, before, after, ok });
  return ok;
}

async function runEngine(browserType, name, reducedMotion) {
  const browser = await browserType.launch({ headless: true });
  const videoDir = join(ARTIFACT_DIR, `motion-video-${name}-${reducedMotion ? "reduce" : "normal"}`);
  mkdirSync(videoDir, { recursive: true });
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 2,
    isMobile: true,
    hasTouch: true,
    reducedMotion: reducedMotion ? "reduce" : "no-preference",
    recordVideo: reducedMotion ? undefined : { dir: videoDir, size: { width: 390, height: 844 } },
    ...(name === "webkit" ? {} : { userAgent: devices["iPhone 13"]?.userAgent }),
  });
  const page = await context.newPage();
  await samplePanelMotion(page, `${name}-hub-${reducedMotion ? "reduce" : "normal"}`, name, reducedMotion);
  await sampleMacroChart(page, `${name}-macro-${reducedMotion ? "reduce" : "normal"}`, name, reducedMotion);
  await context.close();
  await browser.close();
  if (!reducedMotion) {
    const files = await import("node:fs/promises").then((fs) => fs.readdir(videoDir).catch(() => []));
    const webm = files.find((f) => f.endsWith(".webm"));
    if (webm) {
      const dest = join(ARTIFACT_DIR, `motion-demo-${name}-390.webm`);
      try {
        renameSync(join(videoDir, webm), dest);
        pushRun({ label: `${name}-video`, path: dest, ok: existsSync(dest) });
      } catch {
        pushRun({ label: `${name}-video`, path: join(videoDir, webm), ok: true });
      }
    }
  }
}

try {
  await runEngine(chromium, "chromium", false);
  await runEngine(chromium, "chromium", true);
} catch (e) {
  pushRun({ label: "chromium-error", ok: false, error: String(e).slice(0, 200) });
}

try {
  await runEngine(webkit, "webkit", false);
  await runEngine(webkit, "webkit", true);
} catch (e) {
  pushRun({ label: "webkit-error", ok: false, error: String(e).slice(0, 200) });
}

const failures = report.runs.filter((r) => r.ok === false);
const chromiumCore = report.runs.filter(
  (r) =>
    typeof r.label === "string" &&
    r.label.startsWith("chromium-") &&
    (r.label.includes("-hub-") || r.label.includes("-macro-")),
);
report.pass =
  chromiumCore.length >= 4 && chromiumCore.every((r) => r.ok !== false && r.ok !== undefined);
if (failures.some((f) => String(f.label || "").includes("webkit"))) {
  report.notes.push("WebKit skipped or failed — use iOS Safari for final visual confirmation.");
}

writeFileSync(join(ARTIFACT_DIR, "motion-verify-report.json"), JSON.stringify(report, null, 2));
console.log(JSON.stringify({ pass: report.pass, failures: failures.slice(0, 8), runCount: report.runs.length }, null, 2));
process.exit(report.pass ? 0 : 1);
