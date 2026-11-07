# Independent ATS stack (review / pre-deploy)

Two Workers plus one **Durable Object (DO)** class in the **gate** script. The **browser never holds a shared secret**: only the **gate** (`uk-macro-ats-gate`) is exposed to CORS; the **backend** (`uk-macro-ats-backend`) accepts **only** signed `POST /internal/ats` from the gate via a [Workers service binding](https://developers.cloudflare.com/workers/runtime-apis/bindings/service-bindings/).

## Components

| Resource | Wrangler name | Config file | Role |
|----------|---------------|-------------|------|
| Private backend | `uk-macro-ats-backend` | `workers/ats-api/wrangler.backend.toml` | `GEMINI_API_KEY`, HMAC verify, Gemini REST; `workers_dev = false` so **`*.workers.dev` is disabled** (service binding only) |
| Public gate | `uk-macro-ats-gate` | `workers/ats-api/wrangler.toml` | CORS + origin allowlist + DO quota + HMAC forward |
| Quota DO class | `AtsQuota` (in gate bundle) | same as gate | Per-window counters (global + per `CF-Connecting-IP`) |

**Browser calls:** `POST https://<gate-host>/api` (or `/`) — same JSON as today: `{ "mode": "ats"|"cover"|"cvimprove", "cv", "jd" }`.

**Backend URL:** not used from the browser. Only the gate uses `ATS_SERVICE` → `uk-macro-ats-backend`.

## End-to-end flow

1. Browser sends JSON to **gate** with `Origin: https://…` (must match `ATS_ALLOWED_ORIGINS`).
2. Gate checks **fail-closed** config (binding + secret + allowlist + quota namespace).
3. Gate asks **AtsQuota** DO (single global id) whether global and per-IP budgets allow another Gemini call.
4. Gate signs body with **HMAC-SHA256** (`X-ATS-Internal: <timestamp>.<hexsig>`) and `fetch()`es the backend via **service binding** (not public HTTP).
5. Backend verifies HMAC + timestamp skew, then calls Gemini. **No CV/JD text in structured logs** — only lengths and mode.

## Secret and variable **names** (values never in git)

| Name | Where | Purpose |
|------|--------|---------|
| `GEMINI_API_KEY` | **backend only** | Gemini API |
| `ATS_INTERNAL_HMAC_SECRET` | **gate + backend** (same value) | Request signing between Workers (never in browser) |
| `ATS_ALLOWED_ORIGINS` | **gate** | Comma-separated exact origins (**required** for production; gate fails closed if empty) |
| `GEMINI_MODEL` | backend (optional) | Default `gemini-3.8-flash`; see [Gemini API docs](https://ai.google.dev/gemini-api/docs) |
| `ATS_MAX_BODY_CHARS` | gate + backend | Default `120000` |
| `ATS_QUOTA_WINDOW_MS` | **gate** (DO reads `env` for defaults) | Default `86400000` (24h) sliding window for counters |
| `ATS_QUOTA_GLOBAL_PER_WINDOW` | gate | Default `300` successful quota checks → Gemini calls per window (account-wide) |
| `ATS_QUOTA_IP_PER_WINDOW` | gate | Default `20` per `CF-Connecting-IP` per window |
| `ATS_GATE_FAIL_CLOSED` | gate | Default `true` — 503 if binding/secret/quota missing |
| `ATS_QUOTA_DISABLED` | gate | Set `1` **local/tests only** — skips DO (do not use in production) |

**Durable Object:** on **Workers Free**, use `[[migrations]]` with `new_sqlite_classes = ["AtsQuota"]` so the class is created as an **SQLite-backed** Durable Object (Wrangler shows error `10097` if `new_classes` is used instead). See [Wrangler · Durable Objects migrations](https://developers.cloudflare.com/workers/wrangler/configuration/#durable-objects).

## Abuse, cost, and limits

| Control | What it does | What it does **not** do |
|---------|----------------|-------------------------|
| `ATS_ALLOWED_ORIGINS` | Browser `fetch` from unlisted origins gets **403** | Does not stop non-browser callers — use [WAF / Bot](https://developers.cloudflare.com/bots/), [Turnstile](https://developers.cloudflare.com/turnstile/), or other server-side auth for full coverage |
| AtsQuota DO | **Global + per-IP** caps persisted in DO storage (survives restarts) | Not a Google quota; a determined attacker can spread across IPs; still need Google billing alerts |
| HMAC + no public backend URL | Backend ignores unsigned Internet POSTs in normal routing | Mis-routed or leaked backend URLs need **separate** review (keep backend off public routes) |
| Body / field size caps | Reduces token bombs | Does not cap token count inside Gemini |
| `validateAtsShape` + array checks | Rejects some malformed model output | **JSON parsing alone is insufficient** for full schema safety — model can still return misleading content; user must review AI output |

**Paid usage:** each allowed request may call Gemini; pricing and free tier are defined by **Google** at deploy time — not guaranteed here.

## Observability and retention

Wrangler configs include `[observability]` with **Workers Logs** (`invocation_logs = true`) so gate/backend invocations can be queried in the dashboard **after redeploy** — prior deploys without this block may leave no retained log events.

- Gate logs: `kind: ats_gate`, `mode`, `cvLen`, `jdLen`, `ipPresent` (boolean only).
- Backend logs: `kind: ats_backend`, `mode`, `model`, `cvLen`, `jdLen`.
- Upstream Gemini calls use a server-side `AbortController` at **`UPSTREAM_TIMEOUT_MS` (24s)** in `ats-core.ts` — distinct from the static mirror page, which has **no** `AbortController` on browser `fetch`. Timeouts return JSON `{ "error": "upstream_timeout: …" }` with HTTP **502** through the gate (not a bare browser `AbortError`), when the response completes in time.
- Gate logs **`ats_gate_backend`** with `beStatus` after each backend response; binding failures log **`ats_gate_backend_fetch`** without bodies.
- Quota DO stores **numeric counters** and hashed window keys — **not** CV text.
- Log **retention, sampling, and export** are determined by your Cloudflare account (Workers Logs, Logpush, etc.) — configure per policy.

## Deploy order (after explicit approval)

1. Deploy **backend** (creates Worker; `workers_dev = false` keeps it **off** the public `workers.dev` hostname):
   ```bash
   cd workers/ats-api
   npm ci
   npx wrangler secret put ATS_INTERNAL_HMAC_SECRET -c wrangler.backend.toml
   npx wrangler deploy -c wrangler.backend.toml
   ```
2. Deploy **gate** (service binding + Durable Object migration); set **same** `ATS_INTERNAL_HMAC_SECRET`:
   ```bash
   npx wrangler secret put ATS_INTERNAL_HMAC_SECRET -c wrangler.toml
   npx wrangler deploy -c wrangler.toml
   ```
3. **`GEMINI_API_KEY` (parent machine only)** — add the key to **`uk-macro-ats-backend`** using one official path from Cloudflare docs (do not paste the value into chat or commit it):
   - **Wrangler:** `npx wrangler secret put GEMINI_API_KEY -c wrangler.backend.toml` ([Secrets · Workers](https://developers.cloudflare.com/workers/configuration/secrets/))
   - **Dashboard:** **Workers & Pages** → your Worker → **Settings** → **Variables and Secrets** → **Add** → type **Secret**, name **`GEMINI_API_KEY`**, value, then **Deploy** (same page describes this flow).

4. **`ATS_ALLOWED_ORIGINS`** on **`uk-macro-ats-gate`**: list exact browser `Origin` values (comma-separated). For the hub preview, the deployed gate includes  
   `https://uk-macro-analytics-landing.thomasgolloglypagesdev.workers.dev` — add production origins when you cut over. Use `wrangler vars` / dashboard **Variables** (plaintext) to update.

**Always** use `-c workers/ats-api/wrangler.toml` or `-c workers/ats-api/wrangler.backend.toml` — **never** run `wrangler deploy` at repo root for this stack (that deploys `uk-macro-analytics-landing`).

## Rollback

Cloudflare dashboard → each Worker → **Deployments** → roll back to a previous version; or redeploy from an older git SHA.

## Tests (no live Gemini)

```bash
cd workers/ats-api
npm ci
npm test && npm run typecheck
```

Vitest mocks `fetch` for Gemini; gate tests use the **real** backend + HMAC path with mocks.

## Frontend (review)

Hub preview: `static-site/portfolio/config.js` and `config.review-ats-worker.js` both set `AI_BACKEND_URL` to the deployed gate URL (`https://uk-macro-ats-gate.<account-subdomain>.workers.dev/api`). Canonical `tgollogly.dev` portfolio is unchanged.
