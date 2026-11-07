import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import gate from "../src/gate";
import backend from "../src/backend";
import type { GateEnv } from "../src/gate";
import type { BackendEnv } from "../src/backend";
import { signInternalRequest } from "../src/internal-auth";
import { callGeminiText, UPSTREAM_TIMEOUT_MS, validateAtsShape } from "../src/ats-core";

const mockCtx = {
  waitUntil: vi.fn(),
  passThroughOnException: vi.fn(),
} as unknown as ExecutionContext;

function jsonRequest(
  url: string,
  init: RequestInit & { origin?: string },
  body: unknown,
): Request {
  const headers = new Headers(init.headers as HeadersInit);
  headers.set("Content-Type", "application/json");
  if (init.origin) headers.set("Origin", init.origin);
  return new Request(url, {
    method: init.method || "POST",
    headers,
    body: JSON.stringify(body),
  });
}

function makeGateEnv(overrides: Partial<GateEnv> = {}): GateEnv {
  const secret = "test-hmac";
  const be: BackendEnv = {
    GEMINI_API_KEY: "k",
    ATS_INTERNAL_HMAC_SECRET: secret,
  };
  const svc: Fetcher = {
    fetch: (req: Request) => backend.fetch(req, be, mockCtx),
  } as unknown as Fetcher;
  const quota: DurableObjectNamespace = {
    idFromName: () => ({}) as DurableObjectId,
    get: () => ({
      fetch: async () =>
        new Response(JSON.stringify({ allowed: true }), { status: 200, headers: { "Content-Type": "application/json" } }),
    }),
  } as unknown as DurableObjectNamespace;
  return {
    ATS_INTERNAL_HMAC_SECRET: secret,
    ATS_SERVICE: svc,
    ATS_QUOTA: quota,
    ATS_ALLOWED_ORIGINS: "https://hub.example",
    ...overrides,
  };
}

describe("ATS gate", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async () => {
        throw new Error("fetch not mocked");
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("fail-closed 503 when mandatory bindings missing", async () => {
    const env = makeGateEnv({
      ATS_SERVICE: undefined,
    });
    const req = jsonRequest(
      "https://gate.example/api",
      { origin: "https://hub.example" },
      { mode: "ats", cv: "c", jd: "d" },
    );
    const res = await gate.fetch(req, env, mockCtx);
    expect(res.status).toBe(503);
    const j = (await res.json()) as { error: string };
    expect(j.error).toContain("ATS_SERVICE");
  });

  it("403 when Origin not in ATS_ALLOWED_ORIGINS", async () => {
    const env = makeGateEnv();
    const req = jsonRequest(
      "https://gate.example/api",
      { origin: "https://evil.example" },
      { mode: "ats", cv: "c", jd: "d" },
    );
    const res = await gate.fetch(req, env, mockCtx);
    expect(res.status).toBe(403);
  });

  it("403 when Origin header missing (non-browser callers)", async () => {
    const env = makeGateEnv();
    const req = new Request("https://gate.example/api", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: "ats", cv: "c", jd: "d" }),
    });
    const res = await gate.fetch(req, env, mockCtx);
    expect(res.status).toBe(403);
  });

  it("503 when quota denies (global cap)", async () => {
    const quota: DurableObjectNamespace = {
      idFromName: () => ({}) as DurableObjectId,
      get: () => ({
        fetch: async () =>
          new Response(
            JSON.stringify({ allowed: false, scope: "global", retryAfter: 3600 }),
            { status: 200, headers: { "Content-Type": "application/json" } },
          ),
      }),
    } as unknown as DurableObjectNamespace;
    const env = makeGateEnv({ ATS_QUOTA: quota });
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          candidates: [
            { content: { parts: [{ text: '{"score":50,"matched":[],"missing":[],"suggestions":[]}' }] } },
          ],
        }),
        { status: 200 },
      ),
    );
    const req = jsonRequest(
      "https://gate.example/api",
      { origin: "https://hub.example" },
      { mode: "ats", cv: "I know js", jd: "Need k8s" },
    );
    const res = await gate.fetch(req, env, mockCtx);
    expect(res.status).toBe(503);
    const j = (await res.json()) as { error: string };
    expect(j.error).toMatch(/cap reached|global/i);
  });

  it("returns ats scorecard through gate with valid origin + HMAC to backend", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          candidates: [
            {
              content: {
                parts: [{ text: '{"score":82,"matched":["js"],"missing":["k8s"],"suggestions":["add certs"]}' }],
              },
            },
          ],
        }),
        { status: 200 },
      ),
    );
    const env = makeGateEnv();
    const req = jsonRequest(
      "https://gate.example/api",
      { origin: "https://hub.example" },
      { mode: "ats", cv: "I know js", jd: "Need k8s" },
    );
    const res = await gate.fetch(req, env, mockCtx);
    expect(res.status).toBe(200);
    const j = (await res.json()) as {
      score: number;
      matched: string[];
      missing: string[];
      suggestions: string[];
    };
    expect(j.score).toBe(82);
    expect(j.matched).toContain("js");
    expect(res.headers.get("Access-Control-Allow-Origin")).toBe("https://hub.example");
  });

  it("handles concurrent gate requests", async () => {
    vi.mocked(fetch).mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve(
                new Response(
                  JSON.stringify({
                    candidates: [
                      {
                        content: {
                          parts: [{ text: '{"score":60,"matched":[],"missing":[],"suggestions":[]}' }],
                        },
                      },
                    ],
                  }),
                  { status: 200 },
                ),
              ),
            20,
          ),
        ),
    );
    const env = makeGateEnv();
    const reqs = Array.from({ length: 5 }, (_, i) =>
      jsonRequest(
        "https://gate.example/api",
        { origin: "https://hub.example" },
        { mode: "ats", cv: "c" + i, jd: "jd" + i },
      ),
    );
    const results = await Promise.all(reqs.map((r) => gate.fetch(r, env, mockCtx)));
    expect(results.every((r) => r.status === 200)).toBe(true);
  });

  it("rejects malformed JSON", async () => {
    const env = makeGateEnv();
    const req = new Request("https://gate.example/api", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Origin: "https://hub.example",
      },
      body: "{not json",
    });
    const res = await gate.fetch(req, env, mockCtx);
    expect(res.status).toBe(400);
  });

  it("OPTIONS returns 204 for allowed origin", async () => {
    const env = makeGateEnv();
    const req = new Request("https://gate.example/api", {
      method: "OPTIONS",
      headers: { Origin: "https://hub.example" },
    });
    const res = await gate.fetch(req, env, mockCtx);
    expect(res.status).toBe(204);
  });
});

describe("ATS backend (private)", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async () => {
        throw new Error("fetch not mocked");
      }),
    );
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("401 without X-ATS-Internal", async () => {
    const env: BackendEnv = { ATS_INTERNAL_HMAC_SECRET: "sec", GEMINI_API_KEY: "k" };
    const req = new Request("https://internal/internal/ats", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: "ats", cv: "c", jd: "d" }),
    });
    const res = await backend.fetch(req, env, mockCtx);
    expect(res.status).toBe(401);
  });

  it("502 when model JSON shape invalid after parse", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          candidates: [
            {
              content: {
                parts: [{ text: '{"score":50,"matched":"not-an-array","missing":[],"suggestions":[]}' }],
              },
            },
          ],
        }),
        { status: 200 },
      ),
    );
    const secret = "back-hmac";
    const raw = JSON.stringify({ mode: "ats", cv: "c", jd: "d" });
    const sig = await signInternalRequest(secret, "POST", "/internal/ats", raw, Date.now());
    const env: BackendEnv = { ATS_INTERNAL_HMAC_SECRET: secret, GEMINI_API_KEY: "k" };
    const req = new Request("https://internal/internal/ats", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-ATS-Internal": sig },
      body: raw,
    });
    const res = await backend.fetch(req, env, mockCtx);
    expect(res.status).toBe(502);
  });

  it("502 when upstream Gemini fetch aborts (server-side; surfaces as JSON error, not browser fetch throw)", async () => {
    vi.mocked(fetch).mockRejectedValueOnce(
      new DOMException("The operation was aborted.", "AbortError"),
    );
    const secret = "h";
    const raw = JSON.stringify({ mode: "ats", cv: "c", jd: "d" });
    const sig = await signInternalRequest(secret, "POST", "/internal/ats", raw, Date.now());
    const env: BackendEnv = { ATS_INTERNAL_HMAC_SECRET: secret, GEMINI_API_KEY: "k" };
    const req = new Request("https://internal/internal/ats", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-ATS-Internal": sig },
      body: raw,
    });
    const res = await backend.fetch(req, env, mockCtx);
    expect(res.status).toBe(502);
    const j = (await res.json()) as { error: string };
    expect(j.error).toMatch(/aborted/i);
  });

  it("429 when Gemini returns rate limit", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(JSON.stringify({ error: { message: "quota exceeded" } }), { status: 429 }),
    );
    const secret = "h";
    const raw = JSON.stringify({ mode: "ats", cv: "c", jd: "d" });
    const sig = await signInternalRequest(secret, "POST", "/internal/ats", raw, Date.now());
    const env: BackendEnv = { ATS_INTERNAL_HMAC_SECRET: secret, GEMINI_API_KEY: "k" };
    const req = new Request("https://internal/internal/ats", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-ATS-Internal": sig },
      body: raw,
    });
    const res = await backend.fetch(req, env, mockCtx);
    expect(res.status).toBe(429);
  });
});

describe("callGeminiText upstream timeout", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((_url: string, init?: RequestInit) => {
        return new Promise((_, reject) => {
          init?.signal?.addEventListener("abort", () => {
            reject(new DOMException("The operation was aborted.", "AbortError"));
          });
        });
      }),
    );
  });
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it(`aborts Gemini call after UPSTREAM_TIMEOUT_MS (${UPSTREAM_TIMEOUT_MS})`, async () => {
    const pending = callGeminiText("key", "gemini-test", "prompt", 100, 0.1);
    const rejected = expect(pending).rejects.toMatchObject({ name: "AbortError" });
    await vi.advanceTimersByTimeAsync(UPSTREAM_TIMEOUT_MS + 1);
    await rejected;
  });
});

describe("validateAtsShape", () => {
  it("accepts valid object", () => {
    const r = validateAtsShape({
      score: 50,
      matched: ["a"],
      missing: ["b"],
      suggestions: ["c"],
    });
    expect(r.ok).toBe(true);
  });

  it("rejects bad score", () => {
    const r = validateAtsShape({
      score: 101,
      matched: [],
      missing: [],
      suggestions: [],
    });
    expect(r.ok).toBe(false);
  });
});
