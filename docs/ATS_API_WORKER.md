# Independent ATS API Worker (review / future deploy)

This repository includes a **separate** Cloudflare Worker under `workers/ats-api/` that exposes **only** the ATS endpoints used by `static-site/portfolio/ats-matcher.html`:

- `POST /` or `POST /api` with JSON `{ "mode": "ats"|"cover"|"cvimprove", "cv": "...", "jd": "..." }`

It does **not** include chat, job finder, or other portfolio routes. Keeping it in the same repo avoids a second clone and isolates **Gemini billing and abuse surface** from Thomas’s main `portfolio1` Worker.

## Why a dedicated Worker vs extending `portfolio1`

| Approach | Pros | Cons |
|--------|------|------|
| **Dedicated `uk-macro-ats-api`** (this package) | API key and quota isolated; deploy/rollback independent; minimal attack surface (three modes only); hub can point here without touching main site | Extra Worker name and one more secret to set |
| **Extend existing `tgollogly.dev` Worker** | Single deployment | Couples hub demos to main site config; broader blast radius; harder to lock down |

## Configuration (`workers/ats-api/wrangler.toml`)

- **Worker name (proposed):** `uk-macro-ats-api` (`name` in `wrangler.toml`)
- **Entry:** `src/index.ts`
- **Compatibility date:** `2025-11-06` (matches root static landing Worker)

### Secret and variable **names** (no values in git)

| Name | Kind | Purpose |
|------|------|---------|
| `GEMINI_API_KEY` | Secret | Google AI / Gemini API key (server-side only; never sent to the browser) |
| `ATS_API_BEARER_TOKEN` | Optional secret or plain var | If set, `Authorization: Bearer <token>` is **required** on every POST. **CORS is not authentication** — use this for any public `workers.dev` URL before a custom hostname is added. |
| `GEMINI_MODEL` | Optional var | Model id (default `gemini-2.0-flash`; override per [Gemini API docs](https://ai.google.dev/gemini-api/docs)) |
| `ATS_ALLOWED_ORIGINS` | Optional var | Comma-separated exact `Origin` values allowed for browser calls (e.g. preview and production hub URLs). If empty, any origin is accepted (**dev-only** — combine with bearer for staging). |
| `ATS_MAX_BODY_CHARS` | Optional var | Max JSON body length (default `120000`) |
| `ATS_IP_WINDOW_MS` | Optional var | In-isolate rate window in ms (default `60000`) |
| `ATS_IP_MAX_PER_WINDOW` | Optional var | Max POSTs per IP per window (default `30`) |

## Behaviour summary

- **Modes:** `ats` → `{ score, matched, missing, suggestions }`; `cover` / `cvimprove` → `{ text }`.
- **Upstream:** `generateContent` on `generativelanguage.googleapis.com` with `x-goog-api-key` ([Gemini API](https://ai.google.dev/gemini-api/docs)); ~28s fetch timeout; errors returned as JSON `error` (no CV/JD text in logs).
- **Logging:** Structured lines with `kind: "ats_api_request"`, mode, model, **lengths only** (`cvLen`, `jdLen`), boolean `ipPresent`. **No** CV/JD content, keys, or full IP stored in log payloads. Log **retention and sampling** follow your Cloudflare account settings (Workers Logs / Logpush) — not controlled in this repo.
- **Rate limiting:** Best-effort **per isolate** counter by `CF-Connecting-IP`; not a substitute for account-level [Google quota](https://ai.google.dev/gemini-api/docs/rate-limits) or Cloudflare [WAF / Bot Management](https://developers.cloudflare.com/bots/).

## Abuse and cost model (honest)

- **Paid usage:** Every successful POST consumes Gemini tokens; exact cost depends on Google’s **current** pricing and model — verify in Google AI Studio / Cloud billing. This doc does **not** guarantee free tier availability.
- **Unauthenticated public URL + `GEMINI_API_KEY` only:** Anyone who can POST can incur cost. Mitigations implemented here: body size caps, per-IP limit (per isolate), optional bearer token, optional origin allowlist, short upstream timeout.
- **Further hardening (manual):** Turnstile or OAuth in front of the Worker, AI Gateway with budgets, WAF rate rules on the route, or serving only from an auth’d preview.

## Deploy / rollback (only after approval; not run in CI for this branch)

```bash
cd workers/ats-api
npm ci
npx wrangler deploy -c wrangler.toml
```

**Always** pass `-c workers/ats-api/wrangler.toml` so you never hit the repo-root `wrangler.toml` (`uk-macro-analytics-landing`).

**Rollback:** Cloudflare dashboard → Workers → `uk-macro-ats-api` → Deployments → Roll back to previous version; or redeploy an older git SHA.

## Proposed URL shape

- **`https://<subdomain>.<account>.workers.dev/`** (or `/api`) immediately after deploy  
- Optional later: custom hostname (e.g. `ats.example.com`) with its own route — **separate approval**.

## Tests

```bash
cd workers/ats-api
npm ci
npm test
```

Vitest mocks `fetch` to Google — no live Gemini calls, no real CV data.
