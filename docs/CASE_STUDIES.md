# Case studies — junior reporting / data analyst lens

This file ties **evidence in the repository** to what a junior **reporting analyst**, **data analyst**, **data technician**, or **junior BI** hire might look for: sources, quality checks, methods, how to reproduce, **measured** results (from this repo’s outputs), and limits. It does **not** promise job outcomes, senior skills, or contributions beyond what the code and tests document.

Links use paths inside [**uk-macro-analytics-engine**](https://github.com/tgollogly/uk-macro-analytics-engine). Mirrored portfolio demos live under `static-site/portfolio/` (canonical source and deploy). Upstream MIT originals were [**tgollogly/portfolio**](https://github.com/tgollogly/portfolio) (approved for archive — see `docs/PORTFOLIO_REPO_INVENTORY.md`).

---

## 1. UK Macro Analytics Engine (this repo)

### Problem

Make **official UK macro** statistics (inflation and public-sector borrowing) **auditable**: from published CSVs through validation and SQL analytics to charts and exports suitable for review and downstream BI-style tools.

### Sources and snapshot date

- **CPIH all items** (L522) and **PSNB ex banks, monthly £m** (DZLS) via URLs in [`src/config.py`](../src/config.py) (ONS generator CSV endpoints). Crown copyright; **OGL v3** — see [NOTICE.md](../NOTICE.md) and README Legal.
- **Static browser demo** (`static-site/demo/*.json`) is **not live ONS at edge**: it is a **snapshot** with UTC time recorded in [`static-site/demo/manifest.json`](../static-site/demo/manifest.json).

Evidence executed in this workspace (committed files):

| Field | Value |
|--------|--------|
| `generated_at_utc` | `2026-11-06T16:21:46Z` |
| CPIH rows in bundle | 465 |
| PSNB rows in bundle | 354 |
| Latest CPIH with YoY in snapshot | `obs_date` **2026-09-01**, `yoy_pct` **≈ 3.672%** |
| Latest PSNB row in snapshot | `obs_date` **2026-09-01**, `total_net_borrowing_gbp_m` **24520**, `row_count` **1** |

Re-run locally to refresh figures:

```bash
pip install -r requirements-dev.txt
python -m src.data_fetcher ons_cpih_monthly
python -m src.data_fetcher ons_psnb_monthly
python -m src.analytics
python tools/export_demo_assets.py
```

### Data cleaning and quality

- Ingestion and schema expectations are implemented in [`src/data_fetcher.py`](../src/data_fetcher.py) (validated against `DatasetSpec` in config).
- DuckDB views (`db_engine`, `setup_database`) centralise typed tables before analytics.
- `manifest.json` **limitations** array (also surfaced in the browser demo) states e.g. ONS revisions, null YoY at start of series, and that the bundle is a **snapshot**.

### Methods (high level)

- **CPIH:** 3-month rolling average of index, then **YoY %** from 12-month lag (see [`src/analytics.py`](../src/analytics.py) `cpih_rolling_and_yoy`).
- **PSNB:** monthly **sum** of borrowing where multiple rows share a month (`fiscal_monthly_totals`).
- **Streamlit:** Plotly charts, optional refresh pulling CSVs again ([`streamlit_app.py`](../streamlit_app.py)).

### Reproducible checks

```bash
pytest -q
python -m ruff check src tests tools streamlit_app.py
```

CI mirrors this in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml).

### Limitations (honest)

- Figures are **not** an official ONS publication; the publisher may **revise** series.
- The **Workers static demo** does not run Python; it only displays **checked-in JSON** until someone regenerates exports and re-runs `export_demo_assets.py`.
- **SQL Server / Power BI:** optional notes exist ([`docs/SQL_SERVER_MAPPING.md`](./SQL_SERVER_MAPPING.md), [`docs/POWERBI_DESKTOP.md`](./POWERBI_DESKTOP.md)); they are **documentation for using exports**, not proof of a hosted BI deployment inside this repo.

---

## 2a. Monthly macro visual story (`static-site/macro-story.html`)

**Preview-only PR** — not on production until owner publishes. Uses `static-site/demo/macro-story.json` exported via `tools/export_macro_story.py` from the same CPIH/PSNB snapshot. Heatmap (YoY **rate** by calendar month), PSNB monthly bars, partial FY compare, computed findings with “does not prove” limits. Full filters remain in `macro-explorer.html`.

## 2. Static browser demo (`static-site/demo.html`)

### What it shows

Chart.js over `cpih_yoy.json` and `psnb_monthly.json` + provenance from `manifest.json`. **Analyst takeaway:** compare **trend shape** and **last-point KPIs** against publisher tables; download JSON for spreadsheet or BI import testing.

### Distinction vs Streamlit

| Surface | Data freshness | Role |
|--------|----------------|------|
| `demo.html` | Snapshot in git | Fast portfolio / edge preview |
| Streamlit | User-triggered refresh from ONS URLs | Full Python pipeline in one process |

---

## 3. Mirrored portfolio demos (`static-site/portfolio/`)

Upstream MIT licence: [`static-site/portfolio/LICENSE-portfolio.txt`](../static-site/portfolio/LICENSE-portfolio.txt). Behaviour summaries below follow **code paths** visible in the mirror; they are **not** employment claims.

### Beneish M-Score Screener

- **Problem:** Eight-parameter M-Score style screen in the browser for **exploration**.
- **Data:** User-entered or sample figures — **not** filed financial statements from this host; treat as **illustrative** unless you paste real data you’re entitled to use.
- **Methods:** JavaScript implements the usual eight-factor structure on the page.
- **Output:** M-Score and interpretive bands in-browser.

### Heat Anomaly Detector

- **Problem:** Location heat-risk read vs climate baseline with map and radar.
- **Data:** **Live** third-party APIs (Open-Meteo, RainViewer, map tiles per current mirror implementation — see heat page footer and repo `heat-dome.html`).
- **Limits:** External API availability, rate limits, and attribution; not a public-health authority product.

### Thermal Compare

- **Problem:** Compare “feels like” (or related) metrics across locations.
- **Data:** Open-Meteo (keyless in upstream design); third-party requests from the browser.

### Macro trend explorer (this repo)

- **Problem:** Interactive YoY CPIH and PSNB views from committed pipeline exports.
- **Data:** `static-site/demo/*.json` + `manifest.json` (ONS-derived snapshots; not live pull on the static host).
- **Route:** [`macro-explorer.html`](../static-site/portfolio/macro-explorer.html).

### Pipeline coverage explorer (this repo)

- **Problem:** Document snapshot limitations (null YoY start, PSNB row coverage).
- **Data:** Same committed JSON/manifest.
- **Route:** [`data-coverage.html`](../static-site/portfolio/data-coverage.html).

### AI ATS Resume Matcher (retired on public hub)

- **Hub status:** `ats-matcher.html` is informational only — **no** `config.js`, **no** POST from the demo hub.
- **Repo only:** optional Workers documented in [`ATS_API_WORKER.md`](ATS_API_WORKER.md) for developer review.

### BundleBuilder

- **Problem:** Court-bundle style layout / print helpers.
- **Data:** User-entered **fictional** case details in-page; processing in browser per upstream design.

---

## Smallest analyst exercise (uses only this repo’s ONS-derived exports)

**Goal:** Practice **traceability** and a **simple variance** check without adding frameworks.

1. Run the pipeline (see §1) so `data/exports/cpih_yoy.csv` exists.
2. Open the CSV: confirm **last row** `obs_date` and `yoy_pct` match the latest row in `static-site/demo/cpih_yoy.json` **after** you regenerate the demo bundle (they should align when both are from the same run).
3. In a spreadsheet, plot `obs_date` vs `yoy_pct` and compare the **latest** value to the headline CPIH story on [ONS](https://www.ons.gov.uk/) for the same period (publisher wins if they differ — revisions).

**BI gap (genuine):** this repo does **not** ship a `.pbix` or Tableau workbook — only **CSV/JSON/Parquet** and docs for Power BI Desktop. Building a saved report is a separate, optional step on your machine.

---

## 4. Northern Ireland GP prescribing (**rebuilt Nov 2026 — AI-assisted, not historical proof**)

**Label:** Independent recreation in this repo from official Open Data NI CSV. It demonstrates traceability; it does **not** prove prior personal authorship of any earlier notebook.

### Source

| Field | Value |
|--------|--------|
| Dataset | [GP Prescribing Northern Ireland — August 2026](https://admin.opendatani.gov.uk/dataset/gp-prescribing-data/resource/2f8e6dd8-ef10-4442-94db-5e5f74b5c135) |
| Licence | UK Open Government Licence (OGL) |
| Code | [`src/case_studies/prescribing.py`](../src/case_studies/prescribing.py) |
| Checked-in summary | [`static-site/case-studies/ni-prescribing-2026-08-summary.json`](../static-site/case-studies/ni-prescribing-2026-08-summary.json) |
| `generated_at_utc` (summary) | See JSON (`export_case_studies.py`) |
| Input file (local cache, not in git) | `data/cache/case-studies/ni-gp-prescribing-2026-08.csv` |

SHA-256 of the August 2026 CSV is recorded in `static-site/case-studies/manifest.json` after export.

### Recomputed aggregates (August 2026, whole file)

| Measure | Value |
|---------|--------|
| Detail rows | 447,682 |
| Distinct practices | 304 |
| Total items | 3,638,019 |
| Gross cost (£) | 41,961,966.94 |
| Actual cost (£) | 40,416,549.60 |
| BNF ch.4 actual cost (therapy-area shorthand, sometimes called “CNS” in notes) | 7,598,986.45 |
| Tirzepatide items / actual cost | 9,352 / £2,096,263.00 |
| Atorvastatin items / actual cost | 152,303 / £175,013.42 |

### Methods and limits

- DuckDB `read_csv` with **latin-1** encoding and explicit column names (pound sign in headers).
- **Items** are dispensing lines, not patients or events; **Actual cost** is contractor reimbursement, not full NHS spend.
- **BNF chapter 4** = sum of actual cost where `bnf_chapter = 4` in this file (central nervous system chapter in BNF numbering) — a **cost aggregate**, not a diagnosis count.
- **Tirzepatide / atorvastatin** = rows where presentation, VMP, or AMP name contains that string (case-insensitive). Recomputed totals are in JSON; they are **not** independently validated against a separate drug reference list.

**Reproduce:**

```bash
pip install -r requirements.txt
# CSV lands in data/cache/ (gitignored) on first run:
PYTHONPATH=. python tools/export_case_studies.py
pytest tests/test_case_studies_rebuild.py -q
```

---

## 5. UK trade — energy-related CPA (08) lines (**rebuilt Nov 2026 — AI-assisted**)

**Label:** Primary source is [CPA (08) publication tables](https://www.ons.gov.uk/economy/nationalaccounts/balanceofpayments/datasets/publicationtablesuktradecpa08/current) (`cpapublicationq22026august.xlsx`), worksheets **2. Exports quarter** and **4. Imports quarter**, **current prices (CP)**, seasonally adjusted. **CPA (08) is not SITC.** PDF YoY claims are mapped in [`EVIDENCE_HANDOFF.md`](./EVIDENCE_HANDOFF.md); unmatched lines stay **not validated**, not debunked via a different series.

### Source

| Field | Value |
|--------|--------|
| CPA (08) dataset | [Publication tables — CPA 08](https://www.ons.gov.uk/economy/nationalaccounts/balanceofpayments/datasets/publicationtablesuktradecpa08/current) |
| Bulletin context | [UK trade: June 2026](https://www.ons.gov.uk/economy/nationalaccounts/balanceofpayments/bulletins/uktrade/june2026) |
| Code | [`src/case_studies/energy_trade.py`](../src/case_studies/energy_trade.py) |
| Summary JSON | [`static-site/case-studies/uk-energy-trade-q2-2026-summary.json`](../static-site/case-studies/uk-energy-trade-q2-2026-summary.json) |
| SITC substitute (QoQ only) | [Trade publication tables](https://www.ons.gov.uk/economy/nationalaccounts/balanceofpayments/datasets/uktradegoodsandservicespublicationtables/current) sheet `2 - Quarterly CP` |

### Recomputed Q2 2026 vs Q2 2025 YoY (CPA, £bn levels)

| CPA line | Q2 2025 | Q2 2026 | YoY % |
|----------|---------|---------|-------|
| 06.1 Crude petroleum exports | 2.421 | 7.271 | +200.3 |
| 06 Crude petroleum & natural gas imports | 8.551 | 11.680 | +36.6 |
| 19.2 Refined petroleum products imports | 5.327 | 9.239 | +73.4 |
| Total goods exports | 94.721 | 107.153 | +13.1 |
| Total goods imports | 155.278 | 171.197 | +10.3 |

PDF headline **crude exports +109% to £5.4bn** does **not** match CPA **06.1** on this vintage — see claim matrix in JSON `original_pdf_claim_check`.

**Import-growth share (two baskets):** CPA **06 only** import YoY delta ≈ £3.13bn → **~19.7%** of total goods import growth. PDF-style **~44%** uses **CPA 06 + 19.2 refined imports** → **~44.2%** (`cpa_energy_import_growth` in JSON). Do not mix the two denominators.

**Reproduce:** `PYTHONPATH=. python tools/export_case_studies.py` then `pytest tests/test_case_studies_rebuild.py -q`.

**Not published on tgollogly.dev:** Monthly macro story HTML and PR #20-only polish pages — see [`EVIDENCE_HANDOFF.md`](./EVIDENCE_HANDOFF.md) for live vs in-repo-only features.

---

## Readiness vs gaps (evidence-based)

| Area | Evidence in repo | Gap |
|------|------------------|-----|
| ETL + SQL analytics | `src/data_fetcher.py`, `src/analytics.py`, DuckDB | No separate “silver layer” docs beyond governance notes |
| Tests | `pytest` across `tests/` | Not exhaustive of every CSV edge case ONS might publish |
| Dashboards | Streamlit + static Chart.js | Tableau / Power BI artefacts not committed (by design) |
| Portfolio mirrors + macro demos | Static HTML + committed JSON | NI + energy summaries committed; full CSV/xlsx remain local cache |

---

## Migration note (informational only)

Cutover to a custom domain for the seven-demo hub is documented in [`RELEASE_CUTOVER.md`](RELEASE_CUTOVER.md) (plan only). See [`PORTFOLIO_REPO_INVENTORY.md`](PORTFOLIO_REPO_INVENTORY.md) before archiving `tgollogly/portfolio`.
