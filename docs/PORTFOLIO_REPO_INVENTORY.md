# Portfolio repository dependency inventory

This document inventories references to the upstream portfolio repository [**tgollogly/portfolio**](https://github.com/tgollogly/portfolio) inside **uk-macro-analytics-engine**. It supports a **safe archive plan** after domain cutover. **Archive execution:** owner-approved 8 Nov 2026; agent **dependency check passed** (demos + licence in-tree; CI/deploy unaffected). GitHub archive API returned **403** from the cloud-agent token — complete archive manually (Settings → Archive) or with a token that has `admin:repo_hook` / repo admin on `tgollogly/portfolio`.

Broader **keep / archive / merge** mapping (public repos + Workers): [`REPO_CONSOLIDATION_PROPOSAL.md`](REPO_CONSOLIDATION_PROPOSAL.md) (read-only proposal — requires owner approval before any GitHub action).

## Upstream source (verified)

| Item | URL / location |
|------|----------------|
| Canonical upstream | https://github.com/tgollogly/portfolio |
| Licence | MIT (`static-site/portfolio/LICENSE-portfolio.txt`) |
| Mirrored HTML (current) | `beneish.html`, `heat-dome.html`, `thermal-compare.html`, `bundlebuilder.html`, `privacy.html` |
| Retired on hub (local only) | `ats-matcher.html` — informational page; no `config.js`, no POST |
| Authored in this repo (not upstream) | `macro-explorer.html`, `data-coverage.html`, `assets/macro-analytics.js` |

## In-repo references to `tgollogly/portfolio` (committed paths)

| Path | Kind | Action after cutover |
|------|------|----------------------|
| `static-site/index.html` | Attribution + per-demo `blob/main/...` source links | Keep attribution; optional: point `hub-src` links to this repo paths |
| `static-site/portfolio/beneish.html` (and heat, thermal, bundle, privacy) | Footer GitHub icon → portfolio repo | Keep for MIT/upstream honesty until archive |
| `static-site/portfolio/README-SOURCE.md` | Mirror provenance | Update when sync policy changes |
| `static-site/portfolio/config.js` | Comment + gate URL; **not loaded on public hub pages** | Retain for `docs/ATS_API_WORKER.md` / worker dev only |
| `static-site/portfolio/config.review-ats-worker.js` | Review stub | Retain or move under `workers/` docs |
| `docs/CASE_STUDIES.md` | Portfolio mirror note | Already names both repos |
| `static-site/portfolio/LICENSE-portfolio.txt` | MIT copy | **Must keep** while mirrored files ship |

## Runtime / infrastructure **not** the same as deleting the portfolio repo

| Resource | Notes |
|----------|--------|
| Cloudflare Worker `uk-macro-analytics-landing` | Serves `static-site/` from **this** repo |
| Workers `uk-macro-ats-gate`, `uk-macro-ats-backend` | ATS stack in `workers/ats-api/` — **optional**; hub does not expose ATS |
| `tgollogly.dev` / custom domain | **Unknown from this agent** — user must inventory DNS + Pages routes in Cloudflare/Vercel dashboard |

## Recommended safe archive sequence (user-executed)

1. **Merge** hub release to `main` and promote preview that passes CI + browser QA.
2. **Cut over** custom domain to `uk-macro-analytics-landing` (or new Worker/Pages project) per `docs/RELEASE_CUTOVER.md`.
3. **Wait** 2–4 weeks: confirm CVs/portfolio traffic, bookmarks, and job-application links resolve on the new host.
4. **Archive** (not delete) `tgollogly/portfolio` on GitHub with README pointing to `uk-macro-analytics-engine` and the live demo URL.
5. **Optional later:** remove redundant `config.js` from static mirror if ATS workers are decommissioned entirely.

## Known unknowns

- Exact production hostname mapping for `tgollogly.dev` and mail (`longshots`, etc.) — **unchanged by this work**.
- Whether any external site still deep-links to portfolio `ats-matcher.html` with live `config.js`.
- Ongoing need for Gemini gate Workers for non-hub experiments.

## Repo name recommendation

**Keep `uk-macro-analytics-engine`** for job-search URLs and honesty (Python pipeline + static hub). Renaming adds churn without benefit until after cutover.
