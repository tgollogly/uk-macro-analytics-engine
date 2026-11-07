# Read-only contact / email and repo consolidation audit (2026-11-07)

**No DNS changes, no test emails sent, no repos moved or archived.**

## 1. Contact / email on the public site

### Published contact source (in-repo)

| Location | UI | `href` / recipient | Sends mail from site? |
|----------|-----|-------------------|------------------------|
| `static-site/portfolio/privacy.html` | “Questions? Email …” + footer icon | `mailto:thomas@tgollogly.dev` (visible + href match) | **No** — `mailto:` only |
| `static-site/portfolio/beneish.html` | Footer “Email” icon | `mailto:thomas@tgollogly.dev` | **No** |
| `static-site/portfolio/bundlebuilder.html` | Footer “Email” icon | `mailto:thomas@tgollogly.dev` | **No** |
| `static-site/portfolio/heat-dome.html` | Footer “Email” icon | `mailto:thomas@tgollogly.dev` | **No** |
| `static-site/portfolio/thermal-compare.html` | Footer “Email” icon | `mailto:thomas@tgollogly.dev` | **No** |

**No `<form>`** posting email found under `static-site/` (grep). ATS retired page has no mailto. Macro pages (`demo.html`, `index.html`, `macro-explorer.html`, `data-coverage.html`) **do not** expose a contact mailto in current HTML (hub links to GitHub + Privacy).

### Live fetch (workers.dev, 2026-11-07)

| Path | `mailto:` on HTML |
|------|-------------------|
| `/portfolio/privacy.html` | `thomas@tgollogly.dev` |
| `/portfolio/beneish.html` | `thomas@tgollogly.dev` |
| `/portfolio/data-coverage.html` | none |
| `/portfolio/ats-matcher.html` | none |
| `/`, `/demo.html` | none |

**mailto semantics:** Tapping “Email” should open the user’s mail client with **To:** `thomas@tgollogly.dev` — **not proven** here on physical iPhone; agent did not send mail.

**Delivery:** MX/SPF/DKIM indicate **inbound** Cloudflare Email Routing is configured for the zone; **whether `thomas@tgollogly.dev` forwards to your real inbox** was **not** verified (routing rules API returned 403 with current token).

### DNS (read-only)

**Public `dig` (zone apex):**

- MX: `route1–3.mx.cloudflare.net` (priorities 85/86/36)
- TXT SPF: `v=spf1 include:_spf.mx.cloudflare.net ~all`
- DKIM: present at `cf2024-1._domainkey.tgollogly.dev`

**Cloudflare API (read-only, same zone id as `docs/RELEASE_CUTOVER.md`):** MX + SPF TXT match `dig`. Email Routing **rules** list: **403 Authentication error** — destination mailbox not visible from this agent.

### Limits

| Proven | Not proven without you |
|--------|-------------------------|
| Consistent `mailto:thomas@tgollogly.dev` on privacy + 4 portfolio footers | Mail client opens correctly on your iPhone |
| No site-hosted contact form | Message delivered / spam folder / forward target |
| MX → Cloudflare Email Routing | Rule maps `thomas@` → which destination |

---

## 2. “All in one repo” — fact inventory

### `tgollogly/uk-macro-analytics-engine` (this repo) already contains

| Area | Path | Role |
|------|------|------|
| Python macro pipeline | `src/`, `tests/`, DuckDB/Parquet | Source of truth for analytics |
| Public static hub | `static-site/` | All **7 demos** served by `uk-macro-analytics-landing` |
| Hub-authored demos | `demo.html`, `portfolio/macro-explorer.html`, `data-coverage.html`, `assets/macro-analytics.js` | Not from portfolio upstream |
| Portfolio **mirrors** | `portfolio/beneish.html`, `heat-dome.html`, `thermal-compare.html`, `bundlebuilder.html`, `privacy.html` | MIT attribution; copies in-tree |
| Retired ATS **page** | `portfolio/ats-matcher.html` | Static copy only; **no** live POST |
| Optional ATS Workers | `workers/ats-api/` | Deploy **separate**; not linked from public hub |
| Landing Worker config | `wrangler.toml` → `uk-macro-analytics-landing` | Serves `static-site/` |

### Still separate (by design / other hosts)

| Item | Where it lives | Relationship |
|------|----------------|--------------|
| **`tgollogly/portfolio`** | GitHub upstream | Source for mirrored HTML; **not deleted** per prior owner directive |
| **Worker `portfolio1`** | Cloudflare | Rollback host; apex was moved to landing worker |
| **`uk-longshot-finder`** | Cloudflare | `longshots.tgollogly.dev` — unchanged |
| **`uk-macro-ats-gate` / backend** | Cloudflare (optional) | Optional stack; private Python ATS is **not** this public repo |
| **Private Origin repo** `python-ats-matcher` | Cursor private codebase | **Must not** be exposed or copied into public tree |

### Seven demos consolidation status

| # | Demo | In `static-site/` | Upstream portfolio? |
|---|------|-------------------|------------------------|
| 1 | UK macro charts (`demo.html`) | Yes — authored here | No |
| 2 | Macro trend explorer | Yes — authored here | No |
| 3 | Data coverage | Yes — authored here | No |
| 4 | Beneish | Yes — mirror | Yes |
| 5 | Heat dome | Yes — mirror | Yes |
| 6 | Thermal compare | Yes — mirror | Yes |
| 7 | BundleBuilder | Yes — mirror | Yes |

**Recruiter-facing “one site”** is already true for **public demos** (single Worker + `static-site/`). **Git history** for mirrored MIT files still references `tgollogly/portfolio` for honesty.

### Recommended scope (not executed)

| Safe without new approval | Requires explicit owner approval |
|---------------------------|--------------------------------|
| Keep **monorepo**: static hub + Python pipeline + optional Workers in this repo | **Archive** `tgollogly/portfolio` |
| Keep `portfolio1` Worker for rollback | **Delete** Workers or custom domains |
| Document contact only on Privacy + portfolio footers; optionally add mailto to hub footer (copy change) | Point private ATS repo or secrets into public repo |
| Sync mirror HTML occasionally from portfolio | **Merge** Longshots or mail DNS into code deploys |

**“All one repo”** in practice today = **one public repo + one landing Worker** for demos; **portfolio Git repo and Longshots/ATS Workers remain separate runtimes** — that is normal and matches your preserve-mail/Longshots/old-repo instructions.

---

## 3. Motion work (separate track)

Safari-visible motion refinements are authorized on branch `cursor/safari-visible-motion-9407` — not merged at audit time. Current prod: Worker `7384a4c4-64b3-4d47-b07a-420320d3213a`, `main` `1b9948e`.
