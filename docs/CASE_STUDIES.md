# Case studies — junior reporting / data analyst lens

This file ties **evidence in the repository** to what a junior **reporting analyst**, **data analyst**, **data technician**, or **junior BI** hire might look for: sources, quality checks, methods, how to reproduce, **measured** results (from this repo’s outputs), and limits. It does **not** promise job outcomes, senior skills, or contributions beyond what the code and tests document.

Links use paths inside [**uk-macro-analytics-engine**](https://github.com/tgollogly/uk-macro-analytics-engine). Mirrored portfolio demos live under `static-site/portfolio/`; their canonical source is [**tgollogly/portfolio**](https://github.com/tgollogly/portfolio).

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

## Readiness vs gaps (evidence-based)

| Area | Evidence in repo | Gap |
|------|------------------|-----|
| ETL + SQL analytics | `src/data_fetcher.py`, `src/analytics.py`, DuckDB | No separate “silver layer” docs beyond governance notes |
| Tests | `pytest` across `tests/` | Not exhaustive of every CSV edge case ONS might publish |
| Dashboards | Streamlit + static Chart.js | Tableau / Power BI artefacts not committed (by design) |
| Portfolio mirrors + macro demos | Static HTML + committed JSON | Custom domain cutover not executed here |

---

## Migration note (informational only)

Cutover to a custom domain for the seven-demo hub is documented in [`RELEASE_CUTOVER.md`](RELEASE_CUTOVER.md) (plan only). See [`PORTFOLIO_REPO_INVENTORY.md`](PORTFOLIO_REPO_INVENTORY.md) before archiving `tgollogly/portfolio`.
