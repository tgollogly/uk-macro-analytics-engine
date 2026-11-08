# Portfolio demo mirror (source)

**Canonical deploy path:** `static-site/portfolio/` in [**uk-macro-analytics-engine**](https://github.com/tgollogly/uk-macro-analytics-engine) (served at https://tgollogly.dev/).

Static copies of selected pages, originally from [**tgollogly/portfolio**](https://github.com/tgollogly/portfolio) (MIT; owner-approved archive):

- `beneish.html`, `heat-dome.html`, `thermal-compare.html`, `bundlebuilder.html`
- `privacy.html`
- `assets/site.css` (design tokens — do not duplicate `:root` in pages per upstream `README.md`)

**Authored in uk-macro-analytics-engine (not upstream):**

- `macro-explorer.html`, `data-coverage.html`, `assets/macro-analytics.js`

**Retired on the public hub:**

- `ats-matcher.html` — informational stub; live ATS stack is **not** linked from the hub (see `docs/ATS_API_WORKER.md`).

Upstream also includes `assets/chat.js` (site-wide assistant) and `assets/cv-privacy.js`; neither is copied here — only `assets/chat-disabled.js`.

**Upstream licence:** see `LICENSE-portfolio.txt` (MIT, Copyright (c) 2026 Thomas Gollogly per upstream `LICENSE`).

**Hub adjustments (this repo only):**

- `config.js` remains in the tree for worker documentation but is **not** loaded on public hub HTML routes.
- Full `assets/chat.js` is not shipped here; `assets/chat-disabled.js` stub avoids loading the assistant on this hub.

Do not commit API keys. When refreshing mirrored portfolio pages, diff against upstream; macro analytics pages are maintained here.
