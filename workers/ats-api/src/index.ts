/**
 * Standalone ATS API Worker — analyse / cover / cvimprove only (no chat).
 * See ../../docs/ATS_API_WORKER.md for deployment and abuse controls.
 */

export interface Env {
  GEMINI_API_KEY?: string;
  /** Optional: if set, callers must send Authorization: Bearer <token>. CORS is not authentication. */
  ATS_API_BEARER_TOKEN?: string;
  GEMINI_MODEL?: string;
  /** Comma-separated exact origins. Empty = reflect request Origin (allows any browser origin). */
  ATS_ALLOWED_ORIGINS?: string;
  ATS_MAX_BODY_CHARS?: string;
  ATS_IP_WINDOW_MS?: string;
  ATS_IP_MAX_PER_WINDOW?: string;
}

const DEFAULT_MODEL = "gemini-2.0-flash";
const DEFAULT_MAX_BODY = 120_000;
const DEFAULT_WINDOW_MS = 60_000;
const DEFAULT_MAX_PER_IP = 30;

const MAX_CV_CHARS = 60_000;
const MAX_JD_CHARS = 60_000;
const MAX_OUTPUT_ATS = 4096;
const MAX_OUTPUT_DOC = 8192;
const UPSTREAM_TIMEOUT_MS = 28_000;

type Mode = "ats" | "cover" | "cvimprove";

interface AtsJson {
  score: number;
  matched: string[];
  missing: string[];
  suggestions: string[];
}

/** In-isolate sliding window; mitigates bursts (not global account protection). */
const ipHits = new Map<string, { n: number; reset: number }>();

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return handleOptions(request, env);
    }

    if (request.method !== "POST" || (url.pathname !== "/" && url.pathname !== "/api")) {
      return jsonError(request, env, "Method not allowed", 405);
    }

    const originCheck = assertAllowedOrigin(request, env);
    if (!originCheck.ok) {
      return new Response(JSON.stringify({ error: originCheck.error }), {
        status: 403,
        headers: { "Content-Type": "application/json; charset=utf-8" },
      });
    }

    const bearerCheck = requireBearer(request, env);
    if (!bearerCheck.ok) {
      return jsonError(request, env, bearerCheck.error, 401);
    }

    pruneRateLimitMap();

    const ip = request.headers.get("CF-Connecting-IP") || "unknown";
    const rl = checkRateLimit(ip, env);
    if (!rl.ok) {
      return jsonError(request, env, "Too many requests — try again shortly.", 429, { retryAfter: rl.retryAfter });
    }

    const key = (env.GEMINI_API_KEY || "").trim();
    if (!key) {
      return jsonError(request, env, "AI backend not configured (GEMINI_API_KEY).", 503);
    }

    let raw = "";
    try {
      raw = await request.text();
    } catch {
      return jsonError(request, env, "Could not read request body", 400);
    }

    const maxBody = parsePositiveInt(env.ATS_MAX_BODY_CHARS, DEFAULT_MAX_BODY);
    if (raw.length > maxBody) {
      return jsonError(request, env, `Request body too large (max ${maxBody} characters).`, 413);
    }

    let body: unknown;
    try {
      body = raw ? JSON.parse(raw) : null;
    } catch {
      return jsonError(request, env, "Invalid JSON", 400);
    }

    if (!body || typeof body !== "object" || Array.isArray(body)) {
      return jsonError(request, env, "Expected JSON object", 400);
    }

    const o = body as Record<string, unknown>;
    const mode = o.mode;
    if (typeof mode !== "string" || !isMode(mode)) {
      return jsonError(request, env, "mode must be one of: ats, cover, cvimprove", 400);
    }

    const cv = typeof o.cv === "string" ? o.cv.trim() : "";
    const jd = typeof o.jd === "string" ? o.jd.trim() : "";
    if (!jd) {
      return jsonError(request, env, "jd (job description) is required", 400);
    }
    if (!cv) {
      return jsonError(request, env, "cv is required", 400);
    }
    if (cv.length > MAX_CV_CHARS || jd.length > MAX_JD_CHARS) {
      return jsonError(request, env, `cv/jd too long (max ${MAX_CV_CHARS} / ${MAX_JD_CHARS} characters each).`, 413);
    }

    const model = (env.GEMINI_MODEL || DEFAULT_MODEL).trim() || DEFAULT_MODEL;
    ctx.waitUntil(
      Promise.resolve().then(() => {
        console.log(
          JSON.stringify({
            kind: "ats_api_request",
            mode,
            model,
            cvLen: cv.length,
            jdLen: jd.length,
            /** No IP, body text, or key material — sampled Worker logs; retention set by Cloudflare account. */
            ipPresent: ip !== "unknown",
          }),
        );
      }),
    );

    try {
      if (mode === "ats") {
        const parsed = await runAts(env, key, model, cv, jd);
        return jsonOk(request, env, parsed as unknown as Record<string, unknown>);
      }
      if (mode === "cover" || mode === "cvimprove") {
        const text = await runDoc(env, key, model, mode, cv, jd);
        return jsonOk(request, env, { text });
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Upstream error";
      const status =
        /rate|429|quota/i.test(msg) ? 429 : /timeout|aborted|network|fetch/i.test(msg) ? 502 : 502;
      return jsonError(request, env, msg, status);
    }

    return jsonError(request, env, "Unhandled mode", 500);
  },
};

function isMode(s: string): s is Mode {
  return s === "ats" || s === "cover" || s === "cvimprove";
}

function assertAllowedOrigin(request: Request, env: Env): { ok: true } | { ok: false; error: string } {
  const allowed = (env.ATS_ALLOWED_ORIGINS || "").trim();
  if (!allowed) return { ok: true };
  const list = allowed.split(",").map((s) => s.trim()).filter(Boolean);
  if (list.length === 0) return { ok: true };
  const origin = request.headers.get("Origin");
  if (!origin) return { ok: true };
  if (!list.includes(origin)) {
    return {
      ok: false,
      error: "Origin not allowed for this API — update ATS_ALLOWED_ORIGINS or call from an approved site.",
    };
  }
  return { ok: true };
}

function requireBearer(request: Request, env: Env): { ok: true } | { ok: false; error: string } {
  const expected = (env.ATS_API_BEARER_TOKEN || "").trim();
  if (!expected) return { ok: true };
  const h = request.headers.get("Authorization") || "";
  const m = /^Bearer\s+(.+)$/i.exec(h);
  const token = m?.[1]?.trim();
  if (!token || token !== expected) {
    return { ok: false, error: "Unauthorized — missing or invalid bearer token." };
  }
  return { ok: true };
}

/** Prevent the in-isolate rate-limit map from growing without bound on long-lived isolates. */
function pruneRateLimitMap(): void {
  if (ipHits.size <= 2500) return;
  ipHits.clear();
}

function checkRateLimit(ip: string, env: Env): { ok: true } | { ok: false; retryAfter: number } {
  const windowMs = parsePositiveInt(env.ATS_IP_WINDOW_MS, DEFAULT_WINDOW_MS);
  const max = parsePositiveInt(env.ATS_IP_MAX_PER_WINDOW, DEFAULT_MAX_PER_IP);
  const now = Date.now();
  let row = ipHits.get(ip);
  if (!row || now > row.reset) {
    row = { n: 0, reset: now + windowMs };
    ipHits.set(ip, row);
  }
  row.n += 1;
  if (row.n > max) {
    return { ok: false, retryAfter: Math.max(1, Math.ceil((row.reset - now) / 1000)) };
  }
  return { ok: true };
}

function parsePositiveInt(raw: string | undefined, d: number): number {
  if (raw == null || raw === "") return d;
  const n = Number.parseInt(raw, 10);
  return Number.isFinite(n) && n > 0 ? n : d;
}

function corsHeaders(request: Request, env: Env): Record<string, string> {
  const origin = request.headers.get("Origin");
  const allowed = (env.ATS_ALLOWED_ORIGINS || "").trim();
  let allow: string;
  if (allowed) {
    const list = allowed.split(",").map((s) => s.trim()).filter(Boolean);
    if (origin && list.includes(origin)) allow = origin;
    else if (origin) allow = "null";
    else allow = list[0] || "*";
  } else if (origin) {
    /** Requests with `Authorization` are not compatible with `*` — echo the caller origin. */
    allow = origin;
  } else {
    allow = "*";
  }
  const h: Record<string, string> = {
    "Access-Control-Allow-Origin": allow,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Max-Age": "86400",
  };
  h.Vary = "Origin";
  return h;
}

function handleOptions(request: Request, env: Env): Response {
  const originCheck = assertAllowedOrigin(request, env);
  if (!originCheck.ok) {
    return new Response(null, { status: 403 });
  }
  return new Response(null, { status: 204, headers: corsHeaders(request, env) });
}

function jsonError(
  request: Request,
  env: Env,
  error: string,
  status: number,
  extra?: Record<string, unknown>,
): Response {
  const body = JSON.stringify({ error, ...(extra || {}) });
  return new Response(body, {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      ...corsHeaders(request, env),
      ...(status === 429 && extra?.retryAfter ? { "Retry-After": String(extra.retryAfter) } : {}),
    },
  });
}

function jsonOk(request: Request, env: Env, data: Record<string, unknown>): Response {
  return new Response(JSON.stringify(data), {
    status: 200,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      ...corsHeaders(request, env),
    },
  });
}

async function runAts(env: Env, apiKey: string, model: string, cv: string, jd: string): Promise<AtsJson> {
  const prompt = buildAtsPrompt(cv, jd);
  const text = await callGeminiText(env, apiKey, model, prompt, MAX_OUTPUT_ATS, 0.15);
  const parsed = extractJsonObject(text);
  if (!parsed) {
    throw new Error("Model did not return valid JSON for analysis.");
  }
  const score = clampInt(parsed.score, 0, 100);
  const matched = sanitizeStringArray(parsed.matched);
  const missing = sanitizeStringArray(parsed.missing);
  const suggestions = sanitizeStringArray(parsed.suggestions);
  return { score, matched, missing, suggestions };
}

async function runDoc(
  env: Env,
  apiKey: string,
  model: string,
  mode: "cover" | "cvimprove",
  cv: string,
  jd: string,
): Promise<string> {
  const prompt = mode === "cover" ? buildCoverPrompt(cv, jd) : buildCvImprovePrompt(cv, jd);
  return (await callGeminiText(env, apiKey, model, prompt, MAX_OUTPUT_DOC, 0.25)).trim();
}

function buildAtsPrompt(cv: string, jd: string): string {
  return `You are a UK-facing career assistant. Analyse how well the CV matches the job description for applicant tracking systems (ATS).

Rules:
- Output a single JSON object only, no markdown fences, no commentary.
- score is an integer 0-100 (indicative only, not a real ATS).
- matched: keywords or short phrases the CV already reflects (max 20 items).
- missing: important keywords from the job that are absent or weak in the CV (max 20); only list items the applicant could honestly add if true — do not invent experience.
- suggestions: 3-8 short actionable bullet strings.
- Use UK English.
- Never invent employers, dates, degrees or skills the CV does not support.

JSON shape exactly:
{"score":0,"matched":[],"missing":[],"suggestions":[]}

JOB DESCRIPTION:
---
${jd}
---

CV:
---
${cv}
---
`;
}

function buildCoverPrompt(cv: string, jd: string): string {
  return `Write a tailored cover letter for the job below using only facts from the CV. UK English, professional tone.
Rules:
- Do not invent employers, qualifications, dates or skills.
- If the fit is weak, say so briefly and focus on transferable skills that appear in the CV.
- Plain text only — no JSON, no markdown code fences.
- Address the hiring team (no invented hiring manager names).

Job:
---
${jd}
---

CV:
---
${cv}
---
`;
}

function buildCvImprovePrompt(cv: string, jd: string): string {
  return `Rewrite the CV to better reflect the job description while staying truthful. UK English.
Rules:
- Do not invent employers, qualifications, dates or skills.
- Reorder or rephrase for clarity; suggest bullet edits only where supported by the CV.
- Plain text with clear section headings in ALL CAPS lines (e.g. PROFILE, EXPERIENCE).
- No JSON.

Job:
---
${jd}
---

CV:
---
${cv}
---
`;
}

export async function callGeminiText(
  env: Env,
  apiKey: string,
  model: string,
  prompt: string,
  maxTokens: number,
  temperature: number,
): Promise<string> {
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(
    model,
  )}:generateContent`;
  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), UPSTREAM_TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      method: "POST",
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        "x-goog-api-key": apiKey,
      },
      body: JSON.stringify({
        contents: [{ role: "user", parts: [{ text: prompt }] }],
        generationConfig: {
          temperature,
          maxOutputTokens: maxTokens,
        },
      }),
    });
    const raw = await res.text();
    if (!res.ok) {
      let msg = `Gemini HTTP ${res.status}`;
      try {
        const j = JSON.parse(raw) as { error?: { message?: string } };
        if (j.error?.message) msg = j.error.message;
      } catch {
        /* ignore */
      }
      if (res.status === 429) throw new Error(`rate_limited: ${msg}`);
      throw new Error(msg);
    }
    const data = JSON.parse(raw) as {
      candidates?: Array<{ content?: { parts?: Array<{ text?: string }> } }>;
    };
    const text =
      data.candidates?.[0]?.content?.parts?.map((p) => p.text || "").join("") || "";
    if (!text.trim()) throw new Error("Empty model response");
    return text;
  } finally {
    clearTimeout(t);
  }
}

export function extractJsonObject(text: string): Partial<AtsJson> | null {
  const t = text.trim();
  const start = t.indexOf("{");
  const end = t.lastIndexOf("}");
  if (start === -1 || end <= start) return null;
  try {
    const o = JSON.parse(t.slice(start, end + 1)) as Record<string, unknown>;
    return o as Partial<AtsJson>;
  } catch {
    return null;
  }
}

export function clampInt(v: unknown, lo: number, hi: number): number {
  const n = typeof v === "number" ? v : Number.parseInt(String(v), 10);
  if (!Number.isFinite(n)) return lo;
  return Math.max(lo, Math.min(hi, Math.round(n)));
}

export function sanitizeStringArray(v: unknown): string[] {
  if (!Array.isArray(v)) return [];
  const out: string[] = [];
  for (const x of v) {
    if (typeof x !== "string") continue;
    const s = x.trim().slice(0, 200);
    if (s) out.push(s);
    if (out.length >= 24) break;
  }
  return out;
}
