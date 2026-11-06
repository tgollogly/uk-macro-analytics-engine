# Cloudflare Pages — static landing (compatible, non-destructive)

This repo’s **interactive dashboard** is `streamlit_app.py` (long-running Python). **Cloudflare Pages** is appropriate for the **static brochure** in **`static-site/`** only — the same split as Vercel in `docs/VERCEL.md`. Do **not** point an existing production Worker or apex domain here without an explicit cutover plan.

## What gets deployed

| Asset | Cloudflare target | Notes |
|--------|-------------------|--------|
| `static-site/` (HTML/CSS) | **Pages** project | No build step; output = repo subfolder |
| Streamlit app | **Streamlit Community Cloud** (or other Python host) | Not runnable as static Pages |

**No secrets** are required for the static site. Set the dashboard URL in `static-site/index.html` after Streamlit is deployed (replace the primary CTA `href` in the hero).

## Proposed **new** resource names (avoid clashes)

Use a **dedicated** Pages project name so nothing overwrites an existing Worker or zone route:

| Resource | Proposed name | Purpose |
|----------|---------------|---------|
| Cloudflare Pages project | `uk-macro-analytics-landing` | Production-style landing (still a new project) |
| Preview / branch deploys | automatic `*.pages.dev` URLs | PR/branch previews — isolated from production domains |

If the name is taken in your account, use `uk-macro-analytics-engine-landing` or `tgollogly-uk-macro-landing`.

**Do not** reuse names of existing Workers or Pages projects until the parent confirms a cleanup list. This doc assumes **additive** deployment only.

## Dashboard setup (Pages)

1. Cloudflare dashboard → **Workers & Pages** → **Create** → **Pages** → **Connect to Git**.
2. Select **`tgollogly/uk-macro-analytics-engine`** (or your fork).
3. **Build settings:**
   - **Framework preset:** None
   - **Build command:** *(empty)*
   - **Build output directory:** `static-site`
4. Save and deploy. You receive a **`*.pages.dev`** preview URL.

**Custom domain (optional, later):** attach a **new** hostname (e.g. `macro-demo.example.com`) in the Pages project. Do **not** remove or repoint existing apex/production records without explicit approval.

## CLI (optional)

With [Wrangler](https://developers.cloudflare.com/workers/wrangler/install-and-update/) authenticated (`wrangler login` or API token on your machine — **not** available on this agent VM):

```bash
# From repo root; uses ./wrangler.toml
npx wrangler pages deploy static-site --project-name=uk-macro-analytics-landing
```

Use **`--branch`** / preview flows per Cloudflare docs if you want branch-specific URLs without touching production.

## Workers Builds / connector

If the account uses **Workers Builds** with a Git connector: configure the same **output directory** `static-site`, **no** npm build, and the same **new** project name. The connector should **not** delete other repos or Workers — repository fixes stay in Git; deployment is an **additional** target.

## Cleanup boundary

- **In scope here:** document-only + optional `wrangler.toml` for Pages; no DNS edits, no Worker deletes, no domain cutover.
- **Out of scope until confirmed:** removing legacy multi-repo deployments, revoking old integrations, or deleting Cloudflare resources — requires an explicit list from the account owner.

## Verification

- Open the `*.pages.dev` URL: page loads, buttons work, no mixed-content errors.
- Optional: `curl -I https://<project>.pages.dev/` → `200` and `content-type: text/html`.
