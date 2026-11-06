# Proposed privacy / footnote wording (review — not applied to HTML)

These snippets replace references to **`https://tgollogly.dev/api`** with the **independent Worker** once deployed. **Do not** paste into `ats-matcher.html` / `privacy.html` until the Worker URL is final and user approves.

## `ats-matcher.html` — “How it works” / notice paragraph (proposed)

> The front end runs on this static site; when you click analyse or generate, the page POSTs your CV and job description as JSON to **the dedicated ATS Worker URL** configured in `config.js` (not the main portfolio site). That Worker holds the API key server-side and calls Google’s Gemini API. The key is never exposed in the browser.  
> **Privacy:** Google’s retention and processing are governed by Google’s terms; this demo does not store your text in this repository. Do not paste confidential data. For demonstration only — not career or legal advice.

## `ats-matcher.html` / hub footnote (proposed)

> … the ATS matcher sends JSON to **`AI_BACKEND_URL`** (see `config.js`) for Gemini when you click analyse or generate. Backend availability and Google quota are not guaranteed.

## `privacy.html` (proposed alignment)

- State that the mirror may point `AI_BACKEND_URL` at **`uk-macro-ats-api` (Workers)** instead of `tgollogly.dev`, after explicit configuration.  
- Keep existing disclosures: chat disabled on mirror, weather third-party APIs, no audited no-cookie claim unless true.

## Frontend limitation: bearer token

The current page uses **`fetch(url, { body: JSON.stringify(...) })` only**. If `ATS_API_BEARER_TOKEN` is enabled on the Worker, the browser must send **`Authorization: Bearer …`**, which requires a **small script change** (inject header) or a **same-origin route** that adds the header server-side. Document this before enabling bearer on a public demo URL.
