# Evidence handoff — LinkedIn, case studies, and reviewer notes

**Last updated:** 8 November 2026 (Europe/London)

**Site status:** Case studies and hub are **live** on [tgollogly.dev](https://tgollogly.dev/) (deploy via PR #21, Nov 2026). **Monthly macro story** (`macro-story.html`) is **not** published on the static site — Python bundle code may exist in-repo for a future release only.

**Contact:** [LinkedIn](https://www.linkedin.com/in/thomasgollogly) only on the public site. **No public CV PDF** is hosted in this repo or on the landing Worker (by design).

**Rebuild disclaimer:** NI prescribing and UK energy trade are **Nov 2026 AI-assisted recreations** from official files. They demonstrate traceability in this repo; they do **not** prove prior personal authorship of any earlier notebook or PDF.

**Validation fix (parent review):** An early draft wrongly “rejected” a PDF crude-export claim using **SITC 3 Fuels QoQ** — different **commodity** and **period**. This document maps each PDF line to **CPA (08) current prices (CP)**, Q2 **2025 vs Q2 2026** YoY where comparable. **SITC ≠ CPA.** Unmatched PDF lines stay **not validated**, not debunked.

---

## A. Original PDF / screenshot claims → recomputation map

Period for trade: **Q2 2026 vs Q2 2025 YoY** unless noted. Values in **£ billion** from ONS CPA (08) quarterly CP tables (`cpapublicationq22026august.xlsx`). **Do not assume PDF figures are correct.**

| PDF claim (as quoted) | Comparable ONS row | Recomputed Q2 2026 | Recomputed YoY % | Status |
|------------------------|-------------------|--------------------|------------------|--------|
| Crude exports **+109% to £5.4bn** | CPA **06.1 Crude petroleum** exports | **£7.27bn** | **+200.3%** | **Not validated as stated** (level and % differ) |
| Crude+gas imports **+35.8% to £11.7bn** | CPA **06 Crude petroleum & natural gas** imports | **£11.68bn** | **+36.6%** | **Close** |
| Refined imports **+64.8% to £8.9bn** | CPA **19.2 Refined petroleum products** imports | **£9.24bn** | **+73.4%** | **Partial** (level nearer than %) |
| Energy deficit **£10.7bn**, **£2.8bn worse** YoY | Repo: CPA 06 + 19.2 export−import balance | **−£7.67bn** | **+£0.29bn** (less deficit) | **Not validated** (ONS may use wider basket) |
| Energy **+£6.6bn** of **+£15bn** goods imports (**44%**) | CPA imports **06 + 19.2** YoY delta **£7.04bn** ÷ total goods import delta **£15.92bn** | share **~44.2%** | — | **Close on defined basket** (see JSON `cpa_energy_import_growth`) |
| *(CPA **06 only** import YoY delta £3.13bn ÷ £15.92bn)* | *Subset — **not** the PDF basket* | share **~19.7%** | — | **Not comparable to 44% claim** — do not mix with row above |
| Goods exports **£101.7bn**, imports **£171bn** | CPA **Total exports/imports** Q2 2026 | exports **£107.15bn**, imports **£171.20bn** | — | Imports **close**; exports differ |

**Why two import-share figures appear:** **~19.7%** counts only the **CPA 06** crude+gas import line’s YoY change. The prior workbook **~44%** claim matches the wider basket **CPA 06 crude+gas imports plus 19.2 refined imports** (no double-count of 06.1/06.2), which sums to **~£7.04bn** of **£15.92bn** total goods import growth → **~44.2%** in `static-site/case-studies/uk-energy-trade-q2-2026-summary.json`.

**Prior workbook:** Narrative PDF not in repo — lines marked **`not_reproduced_from_cited_workbook`** on pinned ONS vintage, not “wrong because revisions”.

**SITC substitute:** Table 2A QoQ only — reviewer JSON, not public headline.

**Evidence JSON:** `static-site/case-studies/uk-energy-trade-q2-2026-summary.json`.

### Northern Ireland GP prescribing (Aug 2026)

| Claim / slice | Recomputed (full CSV, sha256 in manifest) | Match rule | Status |
|---------------|-------------------------------------------|------------|--------|
| ~3.6m items, ~£40.4m actual | 3,638,019 items; £40,416,549.60 actual | Whole-file DuckDB sum | **Close** |
| 304 practices | 304 distinct `practice` codes | `COUNT(DISTINCT practice)` | **Match** |
| “CNS” therapy-area cost | **£7,598,986.45** actual cost | Sum of **actual cost** where **BNF chapter = 4** (central nervous system chapter in this file — a **cost proxy**, not a patient count) | **Recomputed** — label is shorthand only |
| Tirzepatide | **9,352** items; **£2,096,263** actual | `presentation` / `vmp_nm` / `amp_nm` contains `tirzepatide` (case-insensitive) | **Recomputed** — name match, not validated against an external drug list |
| Atorvastatin | **152,303** items; **£175,013.42** actual | Same contains match for `atorvastatin` | **Recomputed** — name match |

**Tests:** `ni_prescribing_sanity_checks()` cross-checks row counts, period 2026-08, item vs quantity, actual vs gross; full-file recompute when cache present (CI may skip). **Not** fixture-only validation of production totals.

---

## B. Safe to cite in applications (with limits)

1. UK macro pipeline — committed demo JSON + `pytest`.
2. NI prescribing — Open Data NI Aug 2026 CSV, hashed, DuckDB aggregates.
3. UK trade — CPA (08) Q2 YoY recomputation + honest PDF claim matrix (validated / partial / not validated).

Do **not** quote PDF crude **+109% / £5.4bn** unless you independently reconcile to the same CPA series.

---

## C. Application talking points (private CV off-site)

1. Python + DuckDB ONS macro pipeline with CI tests.
2. Rebuilt **NI prescribing** and **CPA (08) energy/trade** summaries with SHA-256 provenance and non-circular tests.
3. Documented **classification and period** limits (CPA vs SITC, CP vs CVM, items vs patients).

---

## D. LinkedIn

Featured → case studies on live hub. Energy bullets should cite **CPA 08** JSON, not PDF headlines. No public CV file on tgollogly.dev.

---

## E. Test execution (repo, Nov 2026)

| Check | Result |
|-------|--------|
| Command | `PYTHONPATH=. pytest -q` — see latest CI / agent run on `main` |
| NI full CSV | **Yes — recomputed** on cached `data/cache/case-studies/ni-gp-prescribing-2026-08.csv` (**447,682** rows) when cache present |
| NI SHA-256 | `8c0b76e3bc41c672a7496756a81647b008ab6d9341b340fca2c859acfd026886` (manifest) |
| ONS vintage | `cpapublicationq22026august.xlsx` + `tradepublicationtables2026aug.xlsx` in local cache |

---

## F. Deployment history (informational)

| Change | Notes |
|--------|--------|
| PR #19 | Case study rebuild (NI + trade), merged earlier Nov 2026 |
| PR #21 | Hub mobile + caption fix, recruiter copy, macro story **removed** from static deploy |

---

## G. Parent follow-ups

1. Original PDF with table/series IDs → extend CPA mapping without forcing numbers.
2. Mention **partial** matches only where JSON `validation` says so.
