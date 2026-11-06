/**
 * Durable Object: account-wide + per-IP token budget for the public gate.
 * Persists counts in DO storage — survives isolate restarts; not a substitute for Google/WAF quotas.
 */

export interface QuotaBindings {
  ATS_QUOTA_WINDOW_MS?: string;
  ATS_QUOTA_GLOBAL_PER_WINDOW?: string;
  ATS_QUOTA_IP_PER_WINDOW?: string;
}

const DEFAULT_WINDOW_MS = 86_400_000; // 24h
const DEFAULT_GLOBAL = 300;
const DEFAULT_IP = 20;

export class AtsQuota implements DurableObject {
  constructor(
    private readonly state: DurableObjectState,
    private readonly env: QuotaBindings,
  ) {}

  async fetch(request: Request): Promise<Response> {
    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }
    let body: { ip?: string };
    try {
      body = (await request.json()) as { ip?: string };
    } catch {
      return json({ allowed: false, error: "invalid_json" }, 400);
    }
    const ip = typeof body.ip === "string" ? body.ip.trim().slice(0, 64) : "unknown";

    const windowMs = parsePositiveInt(this.env.ATS_QUOTA_WINDOW_MS, DEFAULT_WINDOW_MS);
    const globalMax = parsePositiveInt(this.env.ATS_QUOTA_GLOBAL_PER_WINDOW, DEFAULT_GLOBAL);
    const ipMax = parsePositiveInt(this.env.ATS_QUOTA_IP_PER_WINDOW, DEFAULT_IP);
    const now = Date.now();
    const bucket = Math.floor(now / windowMs);
    const windowEnd = (bucket + 1) * windowMs;
    const retryAfterSec = Math.max(1, Math.ceil((windowEnd - now) / 1000));

    const gKey = `g:${bucket}`;
    const iKey = `i:${ip}:${bucket}`;

    let g = (await this.state.storage.get<number>(gKey)) ?? 0;
    let n = (await this.state.storage.get<number>(iKey)) ?? 0;

    if (g >= globalMax) {
      return json({ allowed: false, scope: "global", retryAfter: retryAfterSec }, 200);
    }
    if (n >= ipMax) {
      return json({ allowed: false, scope: "ip", retryAfter: retryAfterSec }, 200);
    }

    g += 1;
    n += 1;
    /** Keys roll forward each window; stale keys remain small — no PII stored. */
    await this.state.storage.put(gKey, g);
    await this.state.storage.put(iKey, n);

    return json({ allowed: true }, 200);
  }
}

function parsePositiveInt(raw: string | undefined, d: number): number {
  if (raw == null || raw === "") return d;
  const n = Number.parseInt(raw, 10);
  return Number.isFinite(n) && n > 0 ? n : d;
}

function json(data: Record<string, unknown>, status: number): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8" },
  });
}
