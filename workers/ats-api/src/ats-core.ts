/**
 * Shared ATS/Gemini logic — used by the private backend Worker only.
 */

export interface AtsJson {
  score: number;
  matched: string[];
  missing: string[];
  suggestions: string[];
}

export type Mode = "ats" | "cover" | "cvimprove";

export const MAX_CV_CHARS = 60_000;
export const MAX_JD_CHARS = 60_000;
export const MAX_OUTPUT_ATS = 4096;
export const MAX_OUTPUT_DOC = 8192;
/** Stay under common ~30s browser/automation fetch cutoffs (gate + quota + Gemini). */
export const UPSTREAM_TIMEOUT_MS = 24_000;

export function isMode(s: string): s is Mode {
  return s === "ats" || s === "cover" || s === "cvimprove";
}

export async function runAts(
  apiKey: string,
  model: string,
  cv: string,
  jd: string,
  generate: typeof callGeminiText,
): Promise<AtsJson> {
  const prompt = buildAtsPrompt(cv, jd);
  const text = await generate(apiKey, model, prompt, MAX_OUTPUT_ATS, 0.15);
  const parsed = extractJsonObject(text);
  if (!parsed) {
    throw new Error("Model did not return valid JSON for analysis.");
  }
  if (
    !Array.isArray(parsed.matched) ||
    !Array.isArray(parsed.missing) ||
    !Array.isArray(parsed.suggestions)
  ) {
    throw new Error("Model returned invalid ATS structure (arrays required).");
  }
  const score = clampInt(parsed.score, 0, 100);
  const matched = sanitizeStringArray(parsed.matched);
  const missing = sanitizeStringArray(parsed.missing);
  const suggestions = sanitizeStringArray(parsed.suggestions);
  return { score, matched, missing, suggestions };
}

export async function runDoc(
  apiKey: string,
  model: string,
  mode: "cover" | "cvimprove",
  cv: string,
  jd: string,
  generate: typeof callGeminiText,
): Promise<string> {
  const prompt = mode === "cover" ? buildCoverPrompt(cv, jd) : buildCvImprovePrompt(cv, jd);
  return (await generate(apiKey, model, prompt, MAX_OUTPUT_DOC, 0.25)).trim();
}

export async function callGeminiText(
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

/** Best-effort shape check after model output — coercion still hides some defects. */
export function validateAtsShape(j: AtsJson): { ok: true } | { ok: false; error: string } {
  if (typeof j.score !== "number" || j.score < 0 || j.score > 100) {
    return { ok: false, error: "invalid score" };
  }
  for (const k of ["matched", "missing", "suggestions"] as const) {
    if (!Array.isArray(j[k])) return { ok: false, error: `invalid ${k}` };
    for (const x of j[k]) {
      if (typeof x !== "string") return { ok: false, error: `non-string in ${k}` };
    }
  }
  return { ok: true };
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
