# Evidence handoff — CV, LinkedIn, and case studies (7 Nov 2026)

**Purpose:** Parent review **before** any publish beyond an open PR. This agent did **not** merge, deploy, or edit LinkedIn. Production remains Worker `73472629` on `https://tgollogly.dev` until you choose otherwise.

**Rebuild disclaimer:** Sections §4–5 below are **new AI-assisted recreations** in `uk-macro-analytics-engine` from official Open Data NI and ONS files. They are **not** evidence that Thomas personally authored earlier notebooks; they prove the **public data supports stated magnitudes** where accepted.

---

## A. LinkedIn screenshot claims vs independent recompute

### Northern Ireland GP prescribing (OpenDataNI / BSO, August 2026)

| Claim (as reported) | Rebuild status | Independent result |
|---------------------|----------------|---------------------|
| ~3.6m prescription **items**, ~£40.4m actual / ~£42m gross | **Accepted (magnitude)** | 3,638,019 items; £40,416,549.60 actual; £41,961,966.94 gross |
| 304 practices | **Accepted** | 304 distinct `practice` values |
| CNS £7.60m, tirzepatide ~£2.1m, atorvastatin 152,303 items | **Accepted (definitions per §4)** | BNF ch.4 actual £7,598,986.45; tirzepatide 9,352 items / £2,096,263 actual; atorvastatin 152,303 items |

**Definitions (pinned):** items ≠ patients; actual cost ≠ discounted NHS system spend; CNS here = BNF chapter 4 actual cost sum.

**Evidence files:** `static-site/case-studies/ni-prescribing-2026-08-summary.json`, `manifest.json` sha256; code `src/case_studies/prescribing.py`.

### UK energy trade (Q2 2026 CPA narrative)

| Claim (as reported) | Rebuild status | Independent result |
|---------------------|----------------|---------------------|
| Large jump in **fuel exports** Q1→Q2 2026 | **Accepted (direction, CPA)** | SITC 3 Fuels exports £7.819bn → £14.276bn (+82.6% QoQ) |
| +109% crude exports, +£5.4bn | **Rejected as stated** | Table row is **all SITC 3 Fuels**, not crude-only; QoQ **+82.6%**, Δ **~£6.5bn** |
| Crude/gas/refined splits, net energy deficit £10.7bn, 44% import growth | **Not recomputed in repo** | Needs additional ONS table rows / bulletin text — not inferred |

**Evidence files:** `static-site/case-studies/uk-energy-trade-q2-2026-summary.json`; parser `src/case_studies/energy_trade.py`.

**Official sources used:**

- [UK trade: June 2026 bulletin](https://www.ons.gov.uk/economy/nationalaccounts/balanceofpayments/bulletins/uktrade/june2026)
- [Publication tables (current)](https://www.ons.gov.uk/economy/nationalaccounts/balanceofpayments/datasets/uktradegoodsandservicespublicationtables/current) → `tradepublicationtables2026aug.xlsx`, sheet `2 - Quarterly CP`

### Health OSINT brief

**Leave off CV and public site** per owner instruction.

---

## B. Verified evidence **in this repo** (safe for site/CV with limits)

| Track | Evidence |
|-------|----------|
| UK macro | `static-site/demo/manifest.json`, `docs/CASE_STUDIES.md` §1, `pytest` |
| NI prescribing | §4 + committed JSON summaries (full CSV cached locally, not in git) |
| UK fuels trade | §5 + committed JSON (full xlsx cached locally) |

**AI assistance (honest):** Hub layout, case-study rebuild code, and this handoff used AI-assisted authoring; **numbers** come from parsers and tests on official files, not model invention.

---

## C. CV-safe bullets (updated after rebuild)

1. Built a **tested Python + DuckDB** pipeline from **ONS CSV endpoints** to reproducible CPIH YoY and PSNB monthly exports, with `pytest`/`ruff` in CI.
2. **Recreated** Northern Ireland **GP prescribing (Aug 2026)** and UK **SITC 3 Fuels trade (Q2 2026 CPA)** from official open data with hashed sources and regression tests (`test_case_studies_rebuild.py`).
3. Shipped **static, evidence-labelled** demos and case-study JSON on the portfolio hub suitable for reviewer inspection without edge Python.
4. Documented **limitations** (items vs patients, CPA vs CVM, snapshot vs live ONS) in `CASE_STUDIES.md` and on-page copy.
5. Deployed macro hub to **Cloudflare Workers** with cache-versioned assets (PR #18) — *this PR does not deploy*.

Use bullets 2–4 with the **rebuild label**; do not imply the NI/energy work predates this repository recreation.

---

## D. LinkedIn — suggestions only (you edit)

| Area | Suggestion |
|------|------------|
| **Featured** | `https://tgollogly.dev/case-studies.html` after you approve PR — cite **verified JSON**, not screenshot PDFs. |
| **About** | One paragraph on traceability; NI/energy **only** with “rebuilt from Open Data NI / ONS tables (Nov 2026)”. |
| **Experience** | Link GitHub case-study summaries; avoid +109% crude export unless you cite ONS crude series you computed. |

Profile: [linkedin.com/in/thomasgollogly](https://www.linkedin.com/in/thomasgollogly).

---

## E. Social / Open Graph (this PR)

- `static-site/og-preview.png`, OG meta on hub pages; run [Post Inspector](https://www.linkedin.com/post-inspector/) after **your** deploy.

---

## F. What this PR changes

1. `src/case_studies/` — prescribing + energy trade parsers.
2. `tools/export_case_studies.py` — download (cache), aggregate, write `static-site/case-studies/*.json`.
3. `docs/CASE_STUDIES.md` §4–5 — verified rebuild text; `docs/EVIDENCE_HANDOFF.md` (this file).
4. `static-site/case-studies.html` — verified summaries linked; rebuild disclaimer.
5. Tests: `test_case_studies_rebuild.py`, fixture CSV head; optional full-file checks when cache present.
6. `requirements.txt` — `openpyxl` for ONS xlsx.

**Not in scope:** merge, `wrangler deploy`, DNS, mail, Longshots, private ATS.

---

## G. Parent optional follow-ups

1. Supply prior PDF/notebook — agent can extend parsers for crude/refined rows **without** forcing totals to match prose.
2. Confirm LinkedIn Featured URL after review.
3. Run `PYTHONPATH=. python tools/export_case_studies.py` after pulling PR to refresh `generated_at_utc`.
