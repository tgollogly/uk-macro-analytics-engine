/**
 * Public ATS gate — browser POSTs here; forwards to private backend via service binding + HMAC.
 * CORS + origin allowlist are not authentication; Durable Object quotas enforce account-wide caps.
 */

import { signInternalRequest } from "./internal-auth";
import { isMode, MAX_CV_CHARS, MAX_JD_CHARS } from "./ats-core";
export { AtsQuota } from "./quota-do";

export interface GateEnv {
  ATS_SERVICE?: Fetcher;
  ATS_QUOTA?: DurableObjectNamespace;
  ATS_INTERNAL_HMAC_SECRET?: string;
  /** Comma-separated; required for browser traffic (fail closed if empty). */
  ATS_ALLOWED_ORIGINS?: string;
  /** If "true", reject when binding/secret/allowlist/quota incomplete (default true). */
  ATS_GATE_FAIL_CLOSED?: string;
  /** Set to "1" in tests only — skips DO (use non-production). */
  ATS_QUOTA_DISABLED?: string;
  ATS_MAX_BODY_CHARS?: string;
}

const INTERNAL_PATH = "/internal/ats";
const DEFAULT_MAX_BODY = 120_000;

export default {
  async fetch(request: Request, env: GateEnv, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    if (request.method === "OPTIONS") {
      return handleOptions(request, env);
    }

    if (request.method !== "POST" || (url.pathname !== "/" && url.pathname !== "/api")) {
      return jsonError(request, env, "Method not allowed", 405);
    }

    const failClosed = (env.ATS_GATE_FAIL_CLOSED || "true").toLowerCase() !== "false";
    if (failClosed) {
      const missing: string[] = [];
      if (!env.ATS_SERVICE) missing.push("ATS_SERVICE binding");
      if (!(env.ATS_INTERNAL_HMAC_SECRET || "").trim()) missing.push("ATS_INTERNAL_HMAC_SECRET");
      if (!(env.ATS_ALLOWED_ORIGINS || "").trim()) missing.push("ATS_ALLOWED_ORIGINS");
      if (!env.ATS_QUOTA && (env.ATS_QUOTA_DISABLED || "").trim() !== "1") {
        missing.push("ATS_QUOTA (Durable Object namespace)");
      }
      if (missing.length) {
        return jsonError(
          request,
          env,
          `Unavailable — gate not fully configured: ${missing.join("; ")}.`,
          503,
        );
      }
    }

    const allowList = parseOriginList(env.ATS_ALLOWED_ORIGINS);
    if (allowList.length === 0) {
      return jsonError(
        request,
        env,
        "Unavailable — ATS_ALLOWED_ORIGINS must list approved hub origins.",
        503,
      );
    }

    const origin = request.headers.get("Origin");
    if (!origin) {
      return jsonError(
        request,
        env,
        "Origin header required — call from an allowed browser origin or use an approved path.",
        403,
      );
    }
    if (!allowList.includes(origin)) {
      return jsonError(
        request,
        env,
        "Origin not allowed — hub URL must be listed in ATS_ALLOWED_ORIGINS.",
        403,
      );
    }

    const secret = (env.ATS_INTERNAL_HMAC_SECRET || "").trim();
    if (!secret) {
      return jsonError(request, env, "Unavailable — internal auth not configured.", 503);
    }

    if (!env.ATS_SERVICE) {
      return jsonError(request, env, "Unavailable — backend service binding missing.", 503);
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
      return jsonError(
        request,
        env,
        `cv/jd too long (max ${MAX_CV_CHARS} / ${MAX_JD_CHARS} characters each).`,
        413,
      );
    }

    const ip = request.headers.get("CF-Connecting-IP") || "unknown";
    const quotaSkip = (env.ATS_QUOTA_DISABLED || "").trim() === "1";
    if (!quotaSkip && env.ATS_QUOTA) {
      const id = env.ATS_QUOTA.idFromName("global");
      const stub = env.ATS_QUOTA.get(id);
      const qr = await stub.fetch(
        new Request("https://quota/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ip }),
        }),
      );
      let quotaJson: { allowed?: boolean; retryAfter?: number; scope?: string; error?: string };
      try {
        quotaJson = (await qr.json()) as typeof quotaJson;
      } catch {
        return jsonError(request, env, "Quota service error", 503);
      }
      if (quotaJson.error) {
        return jsonError(request, env, "Quota service error", 503);
      }
      if (!quotaJson.allowed) {
        const ra = quotaJson.retryAfter ?? 60;
        return jsonError(
          request,
          env,
          `Usage cap reached (${quotaJson.scope ?? "quota"}). Try again after the window resets.`,
          503,
          { retryAfter: ra },
        );
      }
    } else if (!quotaSkip && !env.ATS_QUOTA) {
      return jsonError(request, env, "Unavailable — quota namespace not configured.", 503);
    }

    const ts = Date.now();
    const sig = await signInternalRequest(secret, "POST", INTERNAL_PATH, raw, ts);
    const internalReq = new Request(`https://internal${INTERNAL_PATH}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-ATS-Internal": sig,
      },
      body: raw,
    });

    ctx.waitUntil(
      Promise.resolve().then(() => {
        console.log(
          JSON.stringify({
            kind: "ats_gate",
            mode,
            cvLen: cv.length,
            jdLen: jd.length,
            ipPresent: ip !== "unknown",
          }),
        );
      }),
    );

    let beRes: Response;
    try {
      beRes = await env.ATS_SERVICE.fetch(internalReq);
    } catch (e) {
      const detail = e instanceof Error ? e.message : "backend_unreachable";
      ctx.waitUntil(
        Promise.resolve().then(() => {
          console.log(
            JSON.stringify({
              kind: "ats_gate_backend_fetch",
              mode,
              outcome: "error",
              detail: String(detail).slice(0, 120),
            }),
          );
        }),
      );
      return jsonError(
        request,
        env,
        "Backend service unavailable — no response from private worker.",
        502,
      );
    }

    ctx.waitUntil(
      Promise.resolve().then(() => {
        console.log(
          JSON.stringify({
            kind: "ats_gate_backend",
            mode,
            beStatus: beRes.status,
          }),
        );
      }),
    );

    const headers = new Headers(beRes.headers);
    headers.set("Content-Type", beRes.headers.get("Content-Type") || "application/json; charset=utf-8");
    for (const [k, v] of Object.entries(corsHeadersForOrigin(origin))) {
      headers.set(k, v);
    }
    headers.set("Vary", "Origin");

    return new Response(beRes.body, { status: beRes.status, headers });
  },
};

function parseOriginList(raw: string | undefined): string[] {
  if (!raw || !raw.trim()) return [];
  return raw
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

function parsePositiveInt(raw: string | undefined, d: number): number {
  if (raw == null || raw === "") return d;
  const n = Number.parseInt(raw, 10);
  return Number.isFinite(n) && n > 0 ? n : d;
}

function corsHeadersForOrigin(origin: string): Record<string, string> {
  return {
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400",
  };
}

function handleOptions(request: Request, env: GateEnv): Response {
  const allowList = parseOriginList(env.ATS_ALLOWED_ORIGINS);
  const origin = request.headers.get("Origin");
  if (!origin || !allowList.includes(origin)) {
    return new Response(null, { status: 403 });
  }
  return new Response(null, {
    status: 204,
    headers: corsHeadersForOrigin(origin),
  });
}

function jsonError(
  request: Request,
  env: GateEnv,
  error: string,
  status: number,
  extra?: Record<string, unknown>,
): Response {
  const origin = request.headers.get("Origin");
  const allowList = parseOriginList(env.ATS_ALLOWED_ORIGINS);
  const corsOrigin =
    origin && allowList.includes(origin)
      ? origin
      : allowList[0] || "*";
  const body = JSON.stringify({ error, ...(extra || {}) });
  const headers: Record<string, string> = {
    "Content-Type": "application/json; charset=utf-8",
    "Access-Control-Allow-Origin": corsOrigin,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    Vary: "Origin",
  };
  if (status === 429 || (extra && "retryAfter" in extra)) {
    const ra = extra?.retryAfter;
    if (typeof ra === "number") headers["Retry-After"] = String(ra);
  }
  return new Response(body, { status, headers });
}
