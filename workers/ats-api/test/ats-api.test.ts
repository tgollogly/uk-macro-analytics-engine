import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import worker from "../src/index";
import type { Env } from "../src/index";

const mockCtx = {
  waitUntil: vi.fn(),
  passThroughOnException: vi.fn(),
} as unknown as ExecutionContext;

function jsonRequest(
  url: string,
  init: RequestInit & { origin?: string; auth?: string },
  body: unknown,
): Request {
  const headers = new Headers(init.headers as HeadersInit);
  headers.set("Content-Type", "application/json");
  if (init.origin) headers.set("Origin", init.origin);
  if (init.auth) headers.set("Authorization", init.auth);
  return new Request(url, {
    method: init.method || "POST",
    headers,
    body: JSON.stringify(body),
  });
}

describe("ATS API Worker", () => {
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

  it("rejects disallowed browser origin when ATS_ALLOWED_ORIGINS is set", async () => {
    const env: Env = {
      GEMINI_API_KEY: "test-key",
      ATS_ALLOWED_ORIGINS: "https://allowed.example",
    };
    const req = jsonRequest(
      "https://ats.example/",
      { origin: "https://evil.example" },
      { mode: "ats", cv: "c", jd: "d" },
    );
    const res = await worker.fetch(req, env, mockCtx);
    expect(res.status).toBe(403);
  });

  it("requires bearer when ATS_API_BEARER_TOKEN is set", async () => {
    const env: Env = {
      GEMINI_API_KEY: "k",
      ATS_API_BEARER_TOKEN: "secret-token",
      ATS_ALLOWED_ORIGINS: "https://allowed.example",
    };
    const req = jsonRequest(
      "https://ats.example/",
      { origin: "https://allowed.example" },
      { mode: "ats", cv: "c", jd: "d" },
    );
    const res = await worker.fetch(req, env, mockCtx);
    expect(res.status).toBe(401);
  });

  it("returns 503 when GEMINI_API_KEY is missing", async () => {
    const env: Env = {};
    const req = jsonRequest("https://ats.example/", {}, { mode: "ats", cv: "c", jd: "jd text" });
    const res = await worker.fetch(req, env, mockCtx);
    expect(res.status).toBe(503);
    const j = (await res.json()) as { error: string };
    expect(j.error).toContain("GEMINI_API_KEY");
  });

  it("validates mode and returns ats scorecard from Gemini JSON", async () => {
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
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );

    const env: Env = { GEMINI_API_KEY: "k" };
    const req = jsonRequest(
      "https://ats.example/",
      { origin: "https://hub.example" },
      { mode: "ats", cv: "I know js", jd: "Need k8s" },
    );
    const res = await worker.fetch(req, env, mockCtx);
    expect(res.status).toBe(200);
    const j = (await res.json()) as {
      score: number;
      matched: string[];
      missing: string[];
      suggestions: string[];
    };
    expect(j.score).toBe(82);
    expect(j.matched).toContain("js");
    expect(j.missing).toContain("k8s");
    expect(fetch).toHaveBeenCalled();
    const call = vi.mocked(fetch).mock.calls[0];
    expect(call[0]).toContain("generativelanguage.googleapis.com");
    expect(call[1]?.headers && (call[1].headers as Record<string, string>)["x-goog-api-key"]).toBe("k");
  });

  it("returns cover letter text", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          candidates: [{ content: { parts: [{ text: "Dear hiring team,\n\nI write…" }] } }],
        }),
        { status: 200 },
      ),
    );
    const env: Env = { GEMINI_API_KEY: "k" };
    const req = jsonRequest(
      "https://ats.example/api",
      {},
      { mode: "cover", cv: "Developer", jd: "Role" },
    );
    const res = await worker.fetch(req, env, mockCtx);
    expect(res.status).toBe(200);
    const j = (await res.json()) as { text: string };
    expect(j.text).toContain("Dear hiring team");
  });

  it("rejects oversize body", async () => {
    const env: Env = { GEMINI_API_KEY: "k", ATS_MAX_BODY_CHARS: "100" };
    const big = "x".repeat(200);
    const req = jsonRequest("https://ats.example/", {}, { mode: "ats", cv: big, jd: big });
    const res = await worker.fetch(req, env, mockCtx);
    expect(res.status).toBe(413);
  });
});
