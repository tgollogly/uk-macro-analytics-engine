/**
 * Private ATS backend — invoke only via Worker service binding + HMAC.
 * Not intended for browser calls; no CORS.
 */

import {
  isMode,
  MAX_CV_CHARS,
  MAX_JD_CHARS,
  runAts,
  runDoc,
  callGeminiText,
  validateAtsShape,
} from "./ats-core";
import { verifyInternalRequest } from "./internal-auth";

export interface BackendEnv {
  GEMINI_API_KEY?: string;
  GEMINI_MODEL?: string;
  ATS_INTERNAL_HMAC_SECRET?: string;
  ATS_MAX_BODY_CHARS?: string;
}

const DEFAULT_MODEL = "gemini-2.0-flash";
const DEFAULT_MAX_BODY = 120_000;
const INTERNAL_PATH = "/internal/ats";

export default {
  async fetch(request: Request, env: BackendEnv, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    if (request.method !== "POST" || url.pathname !== INTERNAL_PATH) {
      return new Response(JSON.stringify({ error: "Not found" }), {
        status: 404,
        headers: { "Content-Type": "application/json; charset=utf-8" },
      });
    }

    const secret = (env.ATS_INTERNAL_HMAC_SECRET || "").trim();
    if (!secret) {
      return jsonErr("Backend not configured (ATS_INTERNAL_HMAC_SECRET).", 503);
    }

    let raw = "";
    try {
      raw = await request.text();
    } catch {
      return jsonErr("Could not read request body", 400);
    }

    const auth = await verifyInternalRequest(
      secret,
      "POST",
      INTERNAL_PATH,
      raw,
      request.headers.get("X-ATS-Internal"),
    );
    if (!auth.ok) {
      return jsonErr(auth.error, 401);
    }

    const key = (env.GEMINI_API_KEY || "").trim();
    if (!key) {
      return jsonErr("AI backend not configured (GEMINI_API_KEY).", 503);
    }

    const maxBody = parsePositiveInt(env.ATS_MAX_BODY_CHARS, DEFAULT_MAX_BODY);
    if (raw.length > maxBody) {
      return jsonErr(`Request body too large (max ${maxBody} characters).`, 413);
    }

    let body: unknown;
    try {
      body = raw ? JSON.parse(raw) : null;
    } catch {
      return jsonErr("Invalid JSON", 400);
    }

    if (!body || typeof body !== "object" || Array.isArray(body)) {
      return jsonErr("Expected JSON object", 400);
    }

    const o = body as Record<string, unknown>;
    const mode = o.mode;
    if (typeof mode !== "string" || !isMode(mode)) {
      return jsonErr("mode must be one of: ats, cover, cvimprove", 400);
    }

    const cv = typeof o.cv === "string" ? o.cv.trim() : "";
    const jd = typeof o.jd === "string" ? o.jd.trim() : "";
    if (!jd) {
      return jsonErr("jd (job description) is required", 400);
    }
    if (!cv) {
      return jsonErr("cv is required", 400);
    }
    if (cv.length > MAX_CV_CHARS || jd.length > MAX_JD_CHARS) {
      return jsonErr(
        `cv/jd too long (max ${MAX_CV_CHARS} / ${MAX_JD_CHARS} characters each).`,
        413,
      );
    }

    const model = (env.GEMINI_MODEL || DEFAULT_MODEL).trim() || DEFAULT_MODEL;
    ctx.waitUntil(
      Promise.resolve().then(() => {
        console.log(
          JSON.stringify({
            kind: "ats_backend",
            mode,
            model,
            cvLen: cv.length,
            jdLen: jd.length,
          }),
        );
      }),
    );

    try {
      if (mode === "ats") {
        const parsed = await runAts(key, model, cv, jd, callGeminiText);
        const v = validateAtsShape(parsed);
        if (!v.ok) {
          return jsonErr(`Model output shape invalid: ${v.error}`, 502);
        }
        return jsonOk(parsed as unknown as Record<string, unknown>);
      }
      if (mode === "cover" || mode === "cvimprove") {
        const text = await runDoc(key, model, mode, cv, jd, callGeminiText);
        return jsonOk({ text });
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Upstream error";
      const status =
        /rate|429|quota/i.test(msg) ? 429 : /timeout|aborted|network|fetch/i.test(msg) ? 502 : 502;
      return jsonErr(msg, status);
    }

    return jsonErr("Unhandled mode", 500);
  },
};

function jsonErr(error: string, status: number): Response {
  return new Response(JSON.stringify({ error }), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8" },
  });
}

function jsonOk(data: Record<string, unknown>): Response {
  return new Response(JSON.stringify(data), {
    status: 200,
    headers: { "Content-Type": "application/json; charset=utf-8" },
  });
}

function parsePositiveInt(raw: string | undefined, d: number): number {
  if (raw == null || raw === "") return d;
  const n = Number.parseInt(raw, 10);
  return Number.isFinite(n) && n > 0 ? n : d;
}
