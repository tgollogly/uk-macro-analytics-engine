# Evidence handoff — CV, LinkedIn, and case studies (7 Nov 2026)

**Purpose:** Parent review **before** merge/deploy. Production unchanged.

**Rebuild disclaimer:** NI prescribing and UK energy trade are **Nov 2026 AI-assisted recreations** from official files. They do **not** prove prior personal authorship.

**Validation fix (parent review):** The first PR draft wrongly “rejected” a PDF crude-export claim using **SITC 3 Fuels QoQ** — different **commodity** and **period**. This revision maps each PDF line to **CPA (08) current prices (CP)**, Q2 **2025 vs Q2 2026** YoY where comparable. **SITC ≠ CPA.** Unmatched PDF lines stay **not validated**, not debunked.

---

## A. Original PDF / screenshot claims → recomputation map

Period for trade: **Q2 2026 vs Q2 2025 YoY** unless noted. Values in **£ billion** from ONS CPA (08) quarterly CP tables (`cpapublicationq22026august.xlsx`). **Do not assume PDF figures are correct.**

| PDF claim (as quoted) | Comparable ONS row | Recomputed Q2 2026 | Recomputed YoY % | Status |
|------------------------|-------------------|--------------------|------------------|--------|
| Crude exports **+109% to £5.4bn** | CPA **06.1 Crude petroleum** exports | **£7.27bn** | **+200.3%** | **Not validated as stated** (level and % differ) |
| Crude+gas imports **+35.8% to £11.7bn** | CPA **06 Crude petroleum & natural gas** imports | **£11.68bn** | **+36.6%** | **Close** |
| Refined imports **+64.8% to £8.9bn** | CPA **19.2 Refined petroleum products** imports | **£9.24bn** | **+73.4%** | **Partial** (level nearer than %) |
| Energy deficit **£10.7bn**, **£2.8bn worse** YoY | Repo: CPA 06 + 19.2 export−import balance | **−£7.67bn** | **+£0.29bn** (less deficit) | **Not validated** (ONS may use wider basket) |
| Energy **+£6.6bn** of **+£15bn** goods imports (**44%**) | CPA 06 import delta **£3.13bn** / total goods import delta **£15.92bn** | share **~19.7%** | — | **Not validated as stated** |
| Goods exports **£101.7bn**, imports **£171bn** | CPA **Total exports/imports** Q2 2026 | exports **£107.15bn**, imports **£171.20bn** | — | Imports **close**; exports differ |

**Explicit substitute (not CPA recreation):** SITC 3 Fuels, Table 2A, **QoQ Q1→Q2 2026 only** — exports +82.6% QoQ. Useful context only; **must not** be used to falsify the PDF crude **YoY** line.

**Evidence JSON:** `static-site/case-studies/uk-energy-trade-q2-2026-summary.json` → `original_pdf_claim_check`.

### Northern Ireland GP prescribing (Aug 2026)

| Claim | Status | Recompute (full CSV, sha256 in manifest) |
|-------|--------|-------------------------------------------|
| ~3.6m items, ~£40.4m actual | Close | 3,638,019 items; £40,416,549.60 actual |
| 304 practices | Match | 304 distinct practices |
| CNS / tirzepatide / atorvastatin | Close under §4 definitions | See `ni-prescribing-2026-08-summary.json` |

**Tests:** `ni_prescribing_sanity_checks()` cross-checks row counts, period 2026-08, item vs quantity, actual vs gross; full-file recompute when cache present (CI may skip). **Not** fixture-only validation of production totals.

---

## B. Safe to cite in CV (with limits)

1. UK macro pipeline — committed demo JSON + `pytest`.
2. NI prescribing — Open Data NI Aug 2026 CSV, hashed, DuckDB aggregates.
3. UK trade — CPA (08) Q2 YoY recomputation + honest PDF claim matrix (validated / partial / not validated).

---

## C. CV bullets (revised)

1. Python + DuckDB ONS macro pipeline with CI tests.
2. Rebuilt **NI prescribing** and **CPA (08) energy/trade** summaries with SHA-256 provenance and non-circular tests.
3. Documented **classification and period** limits (CPA vs SITC, CP vs CVM, items vs patients).

Do **not** quote PDF crude **+109% / £5.4bn** unless you independently reconcile to the same CPA series.

---

## D. LinkedIn

Featured → case studies **after** your approval. Energy bullets should cite **CPA 08** JSON, not PDF headlines.

---

## E. PR #19 scope (review only)

- `src/case_studies/energy_trade.py` — CPA (08) primary; SITC substitute labelled.
- `tools/export_case_studies.py` — downloads CPA08 + trade tables + NI CSV.
- Updated handoff, `CASE_STUDIES.md` §5, `case-studies.html` copy.
- QA captures: `case-studies-mobile-375.png`, `case-studies-mobile-400.png` (this branch).

---

## F. Parent follow-ups

1. Original PDF with table/series IDs → extend CPA mapping without forcing numbers.
2. Confirm whether CV should mention **partial** matches only.
