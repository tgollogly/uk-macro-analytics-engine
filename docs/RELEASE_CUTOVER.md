# Release cutover and rollback (plan only)

**Status:** Release candidate on preview Worker — **not** production domain cutover. No DNS or `main` promotion is executed from this document.

## Release candidate scope

| Surface | URL (preview) |
|---------|----------------|
| Static hub + demos | https://uk-macro-analytics-landing.thomasgolloglypagesdev.workers.dev |
| Macro charts | `.../demo.html` |
| New analytics demos | `.../portfolio/macro-explorer.html`, `.../portfolio/data-coverage.html` |

**Excluded from public hub:** ATS submission (`ats-matcher.html` retired; no `config.js` on hub routes).

## Pre-cutover checklist (automated in CI)

- `pytest` (static attribution, macro JSON, workers docs)
- `ruff check`
- Contrast script (if configured in CI)
- `workers/ats-api` vitest (worker stack — not required for hub static deploy)

## Pre-cutover checklist (human / browser)

- 375px and desktop: hub nav **Demos**, seven cards, no ATS submit UI
- Macro explorer: chart + table + CSV; manifest dates visible
- Data coverage: limitations + row counts vs `manifest.json`
- Privacy page: ATS retired wording; no active POST claims
- Heat demo: map tiles load (third-party)

## Production cutover steps (user executes)

1. Merge approved PR to `main`.
2. Deploy landing Worker from `main` (root `wrangler.toml`, name `uk-macro-analytics-landing`).
3. In Cloudflare dashboard: attach **custom domain** (e.g. `www.tgollogly.dev` or apex) to that Worker **or** route traffic per existing Pages setup — **inventory current bindings first**.
4. Verify HTTPS, security headers (Worker defaults), and all internal links (`./demo/`, `../index.html#hub`).
5. Update README / CV links to the custom domain preview URLs.

## Rollback

1. Revert custom domain route to previous target (portfolio Pages, old Worker version, or last-known-good deployment ID).
2. Redeploy previous Worker version: `npx wrangler deployments list` → `npx wrangler rollback --message "..." <version-id>` (landing only).
3. Keep `uk-macro-analytics-engine` `main` at last good commit; hotfix on branch if needed.

**Do not** roll back by deleting Workers or the portfolio repo.

## What stays unchanged (explicit)

- `main` on this repo until user merges
- Portfolio GitHub repo (archive later per `docs/PORTFOLIO_REPO_INVENTORY.md`)
- ATS gate/backend Workers unless user decommissions separately
- Mail and unrelated `tgollogly.dev` resources

## Evidence to attach for job applications

- Preview URL + commit SHA from merged PR
- Screenshot or screen recording of macro explorer + hub (parent browser QA)
- Link to this repo and honest README skills section
