# Proposed privacy / footnote wording (review — not applied to shipped HTML)

## Summary

After deploy, the hub ATS demo would `POST` CV and job text **JSON** to the **public gate Worker** (`uk-macro-ats-gate`) at `AI_BACKEND_URL`. The gate enforces **Origin allowlist**, **usage caps** (Durable Object counters; numeric only, no CV text), and forwards to a **private** backend Worker via **HMAC-signed** service binding. **No shared bearer token in the browser.** The backend holds `GEMINI_API_KEY` and calls Google’s Gemini API; retention follows **Google’s** terms.

**Logs:** Workers may emit **metadata only** (mode, string lengths, `ipPresent` boolean) — not CV/JD content. **Log retention/sampling** is account-level (Cloudflare), not set in this repo.

## `ats-matcher.html` — “How it works” / notice (proposed)

Replace the sentence that names `https://tgollogly.dev/api` with:

> When you click analyse or generate, this page POSTs your CV and job description as JSON to **the URL in `config.js`** (a Cloudflare **gate** Worker on our account). That Worker checks the page origin, applies usage limits, and forwards the request to a **private** backend that holds the API key and calls Google’s Gemini. The key is never exposed in the browser.

## `ats-matcher.html` / footnote (proposed)

> … the ATS matcher sends JSON to **`AI_BACKEND_URL`** (see `config.js`) **for the gate Worker** when you click analyse or generate; the gate forwards to a private Worker that calls Gemini. Data may be processed by Google per their terms. Do not paste confidential information.

## `privacy.html` (proposed)

- Align ATS paragraph with **gate + private backend** (not `tgollogly.dev/api` once switched).
- State that **usage caps** are enforced server-side with **aggregated counters** (no CV storage for quota).

## Limitations (disclose)

- **Origin checks** apply to browsers sending `Origin`; they are not full authentication.
- **Per-IP caps** use `CF-Connecting-IP`; VPNs and distributed traffic can dilute limits.
- **Gate URL** if called without a browser (curl) may still consume quota unless blocked by WAF/other controls you add later.
