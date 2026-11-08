# Repository consolidation proposal (read-only — no GitHub actions taken)

**Date:** 8 Nov 2026 (Europe/London). **Authority:** extends [`PORTFOLIO_REPO_INVENTORY.md`](PORTFOLIO_REPO_INVENTORY.md) and [`READONLY_CONTACT_AND_REPO_AUDIT_2026-11-07.md`](READONLY_CONTACT_AND_REPO_AUDIT_2026-11-07.md).

**Hard stops (unchanged):** no archiving, deleting, renaming, or moving repos; no cross-repo writes; no coordinator repo; **private Origin Python ATS** and **Longshots** and **mail/DNS** stay separate unless you approve otherwise.

## Scope baseline (owner-reported vs agent-verified)

| Source | Finding |
|--------|---------|
| **Owner audit (prior)** | ~**47** GitHub repos owned; **6 public**, **41 private** |
| **This agent (8 Nov 2026)** | `GET /users/tgollogly/repos` returns **6 public** repos (matches your public count). **`/user/repos` → 403** — private inventory not listable from this integration. |

Treat the **41 private repos** as **unaudited here** until you export a list from GitHub Settings or approve a token with `repo` read scope.

## Public GitHub repos — proposed mapping

| Repo | URL | Language (API) | Last push (UTC) | Role vs live site | Proposed action |
|------|-----|----------------|-----------------|-------------------|-----------------|
| **uk-macro-analytics-engine** | https://github.com/tgollogly/uk-macro-analytics-engine | Python | 2026-11-08 | **Source of truth:** `static-site/`, DuckDB pipeline, landing Worker deploy | **KEEP** (canonical) |
| **portfolio** | https://github.com/tgollogly/portfolio | JavaScript | 2026-09-28 | Upstream MIT for mirrored HTML in `static-site/portfolio/`; apex no longer served by `portfolio1` | **KEEP** until mirror parity sign-off → **ARCHIVE** (not delete) with README → `uk-macro-analytics-engine` + https://tgollogly.dev/ |
| **AegisGrid** | https://github.com/tgollogly/AegisGrid | Python | 2026-11-04 | Not linked from tgollogly.dev hub | **KEEP distinct** (review: duplicate of macro work? if yes → **ARCHIVE** after diff) |
| **ReclaimKit** | https://github.com/tgollogly/ReclaimKit | Python | 2026-08-12 | Not on hub | **KEEP distinct** or **ARCHIVE** if superseded — owner review |
| **AnywhereMMS** | https://github.com/tgollogly/AnywhereMMS | JavaScript | 2026-08-10 | Not on hub | **KEEP distinct** or **ARCHIVE** — owner review |
| **TV-Highligts** | https://github.com/tgollogly/TV-Highligts | TypeScript | 2026-09-27 | Not on hub (typo in name) | **KEEP** or rename later with approval — not hub-blocking |

**Merge candidate (only with approval):** `tgollogly/portfolio` → content already in `static-site/portfolio/`; merging git history is **optional** and **not recommended** (MIT licence file + attribution already in-tree).

## Non-GitHub runtimes (dependencies)

| Resource | URL / name | Relationship to hub | Proposed action |
|----------|------------|---------------------|-----------------|
| Worker **uk-macro-analytics-landing** | https://tgollogly.dev/ | Serves `static-site/` from **uk-macro-analytics-engine** | **KEEP** |
| Worker **portfolio1** | Cloudflare (legacy) | Rollback host; apex moved to landing | **KEEP** read-only rollback until owner decommissions |
| Worker **uk-longshot-finder** | https://longshots.tgollogly.dev/ | Separate product | **KEEP** (no merge) |
| Workers **uk-macro-ats-gate** / **backend** | Cloudflare optional | Not linked from public hub; dev/docs only | **KEEP** separate from public tree |
| **Private Origin: python-ats-matcher** | (not public) | ATS experiments | **KEEP private** — never copy into public repo |
| **tgollogly.dev** mail | MX → Cloudflare Email Routing | Portfolio footers use `mailto:` only | **UNCHANGED** — out of this workstream |

## Seven-demo consolidation (already done in-repo)

All recruiter-facing demos ship from **`static-site/`** in **uk-macro-analytics-engine** (see audit §2). Mirrors still cite **portfolio** for MIT provenance only.

## CI / external link dependencies

| Consumer | Depends on |
|----------|------------|
| GitHub Actions in **uk-macro-analytics-engine** | This repo only (`pytest`, Workers review, optional Playwright) |
| Hub `index.html` `hub-src` links | `github.com/tgollogly/portfolio/blob/main/...` (optional future: point to this repo paths) |
| Portfolio footers | `github.com/tgollogly/portfolio` (GitHub icon) — honesty until archive |

## Approval checklist (parent / owner)

1. Confirm **private repo list** (41) — which are legacy forks, course work, or duplicates of macro/portfolio.
2. Approve **archive** of `tgollogly/portfolio` only after 2–4 weeks stable apex on landing Worker.
3. Explicit **no** on merging Longshots, mail, or private ATS into **uk-macro-analytics-engine** unless product decision changes.

## Execution status

**Nothing executed** from this document in agent runs — proposal only.
