# Portfolio demo mirror (source)

Static copies of selected pages from [**tgollogly/portfolio**](https://github.com/tgollogly/portfolio) (MIT):

- `beneish.html`, `heat-dome.html`, `thermal-compare.html`, `bundlebuilder.html`, `ats-matcher.html`
- `privacy.html`
- `assets/site.css` (design tokens — do not duplicate `:root` in pages per upstream `README.md`)

Upstream also includes `assets/chat.js` (site-wide assistant) and `assets/cv-privacy.js`; neither is copied here — only `assets/chat-disabled.js`.

**Upstream licence:** see `LICENSE-portfolio.txt` (MIT, Copyright (c) 2026 Thomas Gollogly per upstream `LICENSE`).

**Hub adjustments (this repo only):**

- `config.js` sets `AI_BACKEND_URL` to the public gate Worker (`uk-macro-ats-gate` on this Cloudflare account); the gate enforces origins and forwards to a private backend Worker for Gemini (see `docs/ATS_API_WORKER.md`).
- Full `assets/chat.js` is not shipped here; `assets/chat-disabled.js` stub avoids loading the assistant on this hub.

Do not commit API keys. Do not use this folder as the source of truth for portfolio — sync from upstream when updating.
