# Release cutover and rollback (plan only — requires separate approval)

**Status:** Production apex `tgollogly.dev` is bound to Worker `uk-macro-analytics-landing` (verified Cloudflare Workers Domains API, 7 Nov 2026 ~13:34 UTC). **No** rebinding, mail, or DNS changes in this doc.

## Resource inventory (read-only API, 7 Nov 2026)

| Resource | Name / hostname | Role today | Cutover impact |
|----------|-----------------|------------|----------------|
| **Production hub Worker** | `uk-macro-analytics-landing` | Serves `tgollogly.dev` + `*.workers.dev` preview host | **Current** production hub; rollback via Worker deployment |
| **Legacy portfolio Worker** | `portfolio1` | No active Workers custom domain on `tgollogly.dev` (API) | **Not** serving apex; do not rebind without explicit approval |
| **Longshots Worker** | `uk-longshot-finder` | `longshots.tgollogly.dev` (workers custom domain) | **Unchanged** — do not rebind |
| **ATS gate/backend** (optional) | `uk-macro-ats-gate`, `uk-macro-ats-backend` | Not linked from public hub on preview | **Unchanged** unless explicitly decommissioned later |
| **Zone** | `tgollogly.dev` (Cloudflare zone id `08afc81b081715e9698b6cd112af9be5`) | DNS + Workers custom domains | User edits routes/domains in dashboard |

### Workers custom domains (zone `tgollogly.dev`)

| Hostname | Binds to Worker | Notes |
|----------|-----------------|-------|
| `tgollogly.dev` | `uk-macro-analytics-landing` | Apex / primary hub (domain id `1d36becf7c31c18cbd5cc5761663429b7c241cb0`) |
| `longshots.tgollogly.dev` | `uk-longshot-finder` | Keep as-is (domain id `bc7ee0babcab0a1f22cd117fc82b64dddd679bde`) |

Per-script **route tables** returned empty from API for `uk-macro-analytics-landing`, `uk-longshot-finder`, and `portfolio1` — apex traffic is driven by **Workers Custom Domains** above, not legacy route patterns.

### DNS records (same zone — mail preserved)

| Type | Name | Purpose |
|------|------|---------|
| MX ×3 | `tgollogly.dev` | Cloudflare Email Routing (`route1–3.mx.cloudflare.net`) — **do not remove** |
| TXT | `tgollogly.dev` | SPF for Cloudflare mail |
| TXT | `cf2024-1._domainkey.tgollogly.dev` | DKIM |
| AAAA (proxied) | `tgollogly.dev` | Apex proxy (`100::`) — works with Workers custom domain |
| AAAA (proxied) | `longshots.tgollogly.dev` | Longshots host |

**Unknown without further audit:** `www.tgollogly.dev`, per-path redirects, Pages projects, or email routing rules beyond MX/SPF/DKIM above.

### GitHub repos (no archive in this plan)

| Repo | Role | After cutover |
|------|------|---------------|
| `tgollogly/uk-macro-analytics-engine` | Source of truth for hub + pipeline | Hub + pipeline URLs point here (no public CV PDF) |
| `tgollogly/portfolio` | Upstream MIT mirror (superseded by in-tree copy) | **Archive approved** — manual step if agent token lacks admin; see `docs/PORTFOLIO_REPO_INVENTORY.md` |

## Preflight (before any production switch)

1. **Merge approved PR** to `main` (not done in agent runs).
2. **Record preview Worker version ID** after final landing deploy:  
   `npx wrangler deployments list` on root `wrangler.toml` (name `uk-macro-analytics-landing`).
3. **Backup current `portfolio1`**: note deployment version in Cloudflare Workers → `portfolio1` → Deployments (or `wrangler deployments list --name portfolio1` if configured).
4. **Confirm** `longshots.tgollogly.dev` still maps to `uk-longshot-finder` after any zone edits.
5. Run **CI green** + **headless hub QA** (`HUB_BROWSER_QA=1 node tools/hub_browser_qa.mjs`) and parent browser sign-off (parent used 400×520; agent uses 375×812 headless).

## Cutover scope (user executes in Cloudflare dashboard)

**Goal:** Serve the seven-demo hub (ATS retired, macro JSON demos) on **`tgollogly.dev`** instead of `portfolio1` content.

**Suggested sequence (custom domain method — exact UI labels may vary):**

1. Deploy `uk-macro-analytics-landing` from **`main`** at the approved commit (same static assets as tested preview).
2. Workers & Pages → `uk-macro-analytics-landing` → **Settings → Domains & Routes** → Add custom domain **`tgollogly.dev`** (or move domain from `portfolio1` per dashboard workflow).
3. Remove or disable **`portfolio1`** binding to `tgollogly.dev` **only after** new binding serves 200 on all hub paths (`/`, `/demo.html`, `/portfolio/macro-explorer.html`, `/favicon.ico`).
4. **Do not** change `longshots.tgollogly.dev`, MX, SPF, or DKIM records.
5. Update README / application links to `https://tgollogly.dev/...` (after verification; `thomas@tgollogly.dev` + LinkedIn — no public CV on the hub).

**Out of scope for cutover:** Streamlit hosting, ATS Worker secrets, Gemini provider calls, deleting `portfolio1` Worker script, archiving GitHub `portfolio` repo.

## Post-cutover verification

| Check | Pass criteria |
|-------|----------------|
| Hub | Seven demo cards, **Demos** nav, ATS retired copy |
| Macro explorer | Chart + CSV full range; table cap message; 6-month range shows 6 rows |
| Data coverage | Manifest limitations visible |
| Privacy | No active ATS POST claims |
| Favicon | `/favicon.ico` HTTP 200 |
| Longshots | `https://longshots.tgollogly.dev` still loads (unchanged Worker) |
| Mail | MX/TXT records unchanged; send test only if user approves |

## Rollback criteria and steps

**Rollback if:** broken apex TLS, wrong Worker served, hub missing demos, mail regression, or longshots broken.

1. Re-bind `tgollogly.dev` custom domain to **`portfolio1`** (last known deployment version from preflight).
2. Or: `npx wrangler rollback` on **`uk-macro-analytics-landing`** if the failure is a bad deploy — **does not** by itself restore `portfolio1` on apex; domain binding must match.
3. Keep preview URL `uk-macro-analytics-landing.thomasgolloglypagesdev.workers.dev` for debugging.
4. Revert `main` only if content regression — prefer Worker rollback first.

## Preview reference (current programme)

| Item | Value |
|------|--------|
| URL | https://uk-macro-analytics-landing.thomasgolloglypagesdev.workers.dev |
| Worker name | `uk-macro-analytics-landing` |
| Deploy config | root `wrangler.toml` → `static-site/` |

Update **commit SHA** and **Worker version ID** in the PR body after each approved landing deploy.

## Editorial hub redesign — live (2026-11-07)

Owner approved publishing the light editorial shell to the **existing** apex (`tgollogly.dev` → `uk-macro-analytics-landing`); no domain rebind, mail, longshots, `portfolio1`, or ATS changes.

| Role | Git `main` | Worker version ID |
|------|------------|-------------------|
| **Rollback (pre-redesign prod)** | `9214880` | `8332de21-4c1f-46d5-b5d8-681fc32bbf66` |
| **Current (post-redesign prod)** | `9b9c0e0` | `f7260861-1dc6-42e2-820a-40756afd8558` |

**PR:** https://github.com/tgollogly/uk-macro-analytics-engine/pull/11

**Rollback steps:** `npx wrangler versions rollback 8332de21-4c1f-46d5-b5d8-681fc32bbf66` on `uk-macro-analytics-landing` (or redeploy from `9214880`). Apex binding unchanged.

**Validation:** `node tools/hub_browser_qa.mjs` — pass on workers.dev; apex may return Cloudflare bot challenge to headless `curl` (verify hub in a normal browser).

## Sitewide contrast fix (2026-11-07)

**Rollback (pre-contrast prod):** `main` `9b9c0e0` / doc `7c3f66c` — Worker `f7260861-1dc6-42e2-820a-40756afd8558`.

Root cause: portfolio `--ink` stayed at dark-theme `#e2e8f0`; Chart.js legend/ticks hard-coded to slate. Fixed via `var(--hub-text)`, `chart-light-theme.js`, and rendered-route contrast in `tools/hub_browser_qa.mjs`.

## Dashboard-inspired panels + motion (2026-11-07)

**Rollback (pre motion/orca pass):** Worker `58ffd470-5c57-429c-94b5-564bf299bda5` / `main` `41a4cf4`.

Visual reference: [Orca Sales Management Dashboard (Dribbble)](https://dribbble.com/shots/23470931-Orca-Sales-Management-Dashboard) — page 403 in agent `curl`; Playwright captured a Dribbble **browse** grid, not the shot art. Patterns applied **originally**: cool gray canvas, white elevated panels, left accent rail, KPI insight cards, chart update animation (`chart.update('active')`), `hub-motion.css` view-transition meta (Chromium), `prefers-reduced-motion` off switch.

Dribbble reference capture: `/opt/cursor/artifacts/orca-dribbble-reference.png` (browse fallback — not copied pixels).

| Role | Git `main` | Worker version ID |
|------|------------|-------------------|
| **Rollback (pre motion/orca pass)** | `41a4cf4` | `58ffd470-5c57-429c-94b5-564bf299bda5` |
| **Current** | `17450d7` | `7384a4c4-64b3-4d47-b07a-420320d3213a` |

**PR:** #13

## Safari-visible motion (2026-11-07)

**Rollback (pre Safari-visible motion):** `main` `1b9948e` — Worker `7384a4c4-64b3-4d47-b07a-420320d3213a`.

**Current:** `main` `281cf17` — Worker `73472629-4495-417c-abc2-5697c2f108d2` (**PR #18** cache + macro explorer).

**Rollback (pre cache fix):** `main` `c8838cb` — Worker `aace6545-ae4e-4452-bc2d-2285fcb09726` (**PR #16**).

**Rollback (pre-PR16):** `main` `fdaa4e7` — Worker `54f689cd-e46b-4900-bc07-68c9f851686b` (**PR #15**).

Documented in `docs/STORY_EFFECTS_REFERENCE.md`. Physical iPhone Safari not verified; Playwright WebKit blocked in agent VM (missing OS deps).

`initPageMotion()` + `body.is-motion-on`, 780ms panel enter, 750ms Chart.js updates, `tools/motion_verify.mjs`.

## Automated checks (repo)

- `pytest` (includes static/macro attribution; optional `HUB_BROWSER_QA=1` Playwright gate)
- `ruff check`
- `python tools/check_hub_contrast.py` (token pairs, not full page audit)
- `python src/security_audit.py`, `pip-audit`
- `workers/ats-api` vitest (ATS stack; hub deploy does not require redeploying gate/backend)

## Evidence for job applications

- Preview URL + commit SHA + Worker version ID
- Screenshots: `/opt/cursor/artifacts/hub-mobile375.png`, `hub-desktop.png`, `macro-explorer-desktop.png` (from `tools/hub_browser_qa.mjs`)
- Honest limits: headless 375px ≠ parent Chrome 400px; no WCAG certification — contrast script + spot checks only
