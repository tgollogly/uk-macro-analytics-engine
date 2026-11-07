# Release cutover and rollback (plan only — requires separate approval)

**Status:** Preview release candidate on Worker `uk-macro-analytics-landing` — **no** production hostname cutover, **no** `main` merge, **no** portfolio archive, **no** mail/DNS edits in this doc.

## Resource inventory (read-only API, 7 Nov 2026)

| Resource | Name / hostname | Role today | Cutover impact |
|----------|-----------------|------------|----------------|
| **Production portfolio Worker** | `portfolio1` | Serves current `tgollogly.dev` static portfolio | **Would be replaced or bypassed** when apex points at new hub |
| **Preview hub Worker** | `uk-macro-analytics-landing` | `https://uk-macro-analytics-landing.thomasgolloglypagesdev.workers.dev` | **Target** for approved cutover |
| **Longshots Worker** | `uk-longshot-finder` | `longshots.tgollogly.dev` (workers custom domain) | **Unchanged** — do not rebind |
| **ATS gate/backend** (optional) | `uk-macro-ats-gate`, `uk-macro-ats-backend` | Not linked from public hub on preview | **Unchanged** unless explicitly decommissioned later |
| **Zone** | `tgollogly.dev` (Cloudflare zone id `08afc81b081715e9698b6cd112af9be5`) | DNS + Workers custom domains | User edits routes/domains in dashboard |

### Workers custom domains (zone `tgollogly.dev`)

| Hostname | Binds to Worker | Notes |
|----------|-----------------|-------|
| `tgollogly.dev` | `portfolio1` | Apex / primary portfolio host today |
| `longshots.tgollogly.dev` | `uk-longshot-finder` | Keep as-is |

Per-script **route tables** returned empty from API for `portfolio1`, `uk-macro-analytics-landing`, and `uk-longshot-finder` — traffic for the apex is driven by **Workers Custom Domains** above, not legacy route patterns (verify in dashboard before change).

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
| `tgollogly/uk-macro-analytics-engine` | Source of truth for hub + pipeline | CV links point here |
| `tgollogly/portfolio` | Upstream MIT mirror for some HTML | **Archive later** with README pointer — see `docs/PORTFOLIO_REPO_INVENTORY.md` |

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
5. Update CV/README external links to `https://tgollogly.dev/...` (after verification).

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
