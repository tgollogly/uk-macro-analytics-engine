<h1 align="center">UK Macro Analytics Engine</h1>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.11+-2563eb?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11+" /></a>
  &nbsp;
  <a href="https://duckdb.org/"><img src="https://img.shields.io/badge/DuckDB-OLAP-fbbf24?style=for-the-badge&logo=duckdb&logoColor=0f172a" alt="DuckDB" /></a>
  &nbsp;
  <a href="https://streamlit.io/"><img src="https://img.shields.io/badge/Streamlit-Dashboard-ff4b4b?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit" /></a>
</p>

<p align="center">
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-22c55e?style=flat-square" alt="MIT License" /></a>
  <a href="./NOTICE.md"><img src="https://img.shields.io/badge/Data-OGL%20v3-0ea5e9?style=flat-square" alt="Open Government Licence" /></a>
  <a href="./.github/workflows/ci.yml"><img src="https://img.shields.io/badge/CI-GitHub%20Actions-181717?style=flat-square&logo=github" alt="CI" /></a>
</p>

<p align="center">
  <em>Portfolio · Python · open ONS data · validation · DuckDB · dashboards</em><br/>
  <strong>Thomas Gollogly</strong>
</p>

<p align="center">
  <!-- Explicit ./ link keeps “open image” on the same branch/PR; bare <img> often links to default branch. -->
  <!-- ?v= bumps GitHub’s image CDN when the PNG bytes change (otherwise it can look “stuck”). -->
  <a href="./hero.png?v=6" title="hero.png (this branch)">
    <img
      src="./hero.png?v=6"
      alt="UK Macro Analytics Engine banner"
      width="100%"
      decoding="async"
      fetchpriority="high"
    />
  </a>
</p>

> **What this is** — A **Python 3.11+** pipeline that downloads **UK open macro** CSVs from the ONS, **validates** structure, caches **Parquet**, loads **DuckDB**, runs **SQL analytics** (rolling averages, YoY inflation, fiscal series), and serves a **Streamlit** portfolio dashboard with optional static/Vercel landing page.

---

## Contents

| Section | What you get |
|---------|----------------|
| [**Architecture**](#architecture) | Flow + diagram assets |
| [**Tech stack**](#tech-stack) | Libraries and roles |
| [**Portfolio dashboard**](#portfolio-dashboard-streamlit--free-locally) | Streamlit + Vercel notes |
| [**Quick start**](#getting-started) | Install & CLI |
| [**Config**](#configuration) | URLs, DuckDB, cache |
| [**Security & compliance**](#security--compliance) | Audit, secrets, licences |
| [**CI & tests**](#continuous-integration) | GitHub Actions |
| [**Legal**](#legal-licence--disclaimer) | MIT, OGL, disclaimers |

---

## Architecture

**Flow** — readable everywhere (GitHub web & mobile):

<pre>
┌──────────────────────────────────────────┐
│ Ingest: requests → data_fetcher → Parquet │
└───────────────────┬──────────────────────┘
                    ▼
┌──────────────────────────────────────────┐
│ DuckDB: db_engine, views (CPIH / PSNB)    │
└───────────────────┬──────────────────────┘
                    ▼
┌──────────────────────────────────────────┐
│ analytics.py: SQL, YoY, rolling, exports  │
└───────────────────┬──────────────────────┘
                    ▼
┌──────────────────────────────────────────┐
│ Outputs: Parquet · CSV · JSON · report   │
│ Optional: Streamlit · static-site/Vercel  │
└──────────────────────────────────────────┘
</pre>

<p align="center">
  <a href="./architecture.png?v=6" title="architecture.png (this branch)">
    <img
      src="./architecture.png?v=6"
      alt="Architecture diagram: Ingestion, DuckDB, Analytics, Exports"
      width="100%"
      loading="lazy"
      decoding="async"
    />
  </a>
</p>

<p align="center"><sub>PNG bitmap for README (<code>python3 tools/regen_readme_images.py</code> also writes WebP); <strong>vector</strong>: <a href="./architecture.svg">architecture.svg</a> · <strong>Mermaid source</strong> (desktop): <a href="./docs/architecture.mmd">docs/architecture.mmd</a></sub></p>

---

## Tech stack

| Area | Stack |
|------|--------|
| **Runtime** | Python **3.11+** (CI: 3.11 & 3.12) |
| **Storage / SQL** | **DuckDB** (views, optional indexes) |
| **Tables** | **pandas**, **pyarrow** (Parquet) |
| **HTTP** | **requests** (retries, timeouts) |
| **Dashboard** | **Streamlit**, **Plotly** |
| **Quality** | **ruff**, **pytest**, `security_audit.py` |
| **CI** | **GitHub Actions** |

---

## Portfolio dashboard (Streamlit — free locally)

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

| Feature | Detail |
|---------|--------|
| **Charts** | Plotly line charts, dark theme |
| **Data** | **Refresh** pulls latest ONS CSV from URLs in `src/config.py` (batch, not a socket) |
| **Host (free)** | [Streamlit Community Cloud](https://streamlit.io/cloud) · see [**docs/STREAMLIT.md**](./docs/STREAMLIT.md) |

### Landing page on Vercel

Streamlit needs a **long-running Python app** — not Vercel serverless by default. Use **`static-site/`** on [**Vercel**](https://vercel.com) and link to your Streamlit URL: [**docs/VERCEL.md**](./docs/VERCEL.md).

### More docs (free tooling)

- [**Data governance**](./docs/DATA_GOVERNANCE.md) · [**T-SQL notes**](./docs/SQL_SERVER_MAPPING.md) · [**Power BI Desktop**](./docs/POWERBI_DESKTOP.md)
- **Static HTML report:** `python -m src.report_builder`

---

## Getting started

### Prerequisites

- **Python 3.11+**
- Network access for ONS downloads (or supply your own Parquet via `DatasetSpec`)

### Install (with dev/lint tools)

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

Use **`requirements.txt`** only if you do not need **ruff** locally.

### CLI quickstart

| Step | Command |
|------|---------|
| 1 · Fetch CPIH | `python -m src.data_fetcher ons_cpih_monthly` |
| 2 · Fetch PSNB | `python -m src.data_fetcher ons_psnb_monthly` |
| 3 · Run analytics | `python -m src.analytics` |
| 4 · Optional HTML report | `python -m src.report_builder --open` |

**Exports** (under `data/exports/`, gitignored): `cpih_yoy` / `psnb_monthly` as **Parquet**, **JSON**, **CSV**; `report.html` after step 4.

---

## Configuration

| Topic | Location |
|-------|----------|
| Dataset URLs & columns | `src/config.py` → `DATASETS` |
| DuckDB tuning | `src/config.py` → `DuckDBSettings` |
| Cache | `data/cache/parquet/` (auto-created) |

If a publisher changes CSV layout, update **`DatasetSpec`** or **`_alias_key_columns`** in `src/data_fetcher.py`.

---

## Security & compliance

| Topic | Detail |
|-------|--------|
| **Dependencies** | Pinned in `requirements.txt`; CI runs `src/security_audit.py` |
| **Secrets** | Do not commit keys; audit flags risky patterns |
| **Software** | **MIT** — see [`LICENSE`](./LICENSE) |
| **Statistics** | Often **OGL**; see [`NOTICE.md`](./NOTICE.md) |

---

## Continuous integration

Workflow: [`.github/workflows/ci.yml`](./.github/workflows/ci.yml)

1. `python -m ruff check src tests tools`
2. `python src/security_audit.py`
3. `python -m compileall -q src tests`
4. `pytest -q --tb=short`

```bash
pytest -q
```

---

## Project layout

```
.
├── streamlit_app.py          # Streamlit portfolio dashboard
├── static-site/              # Vercel-ready landing (HTML)
├── src/                      # Pipeline package
├── tests/
├── docs/                     # Architecture, governance, Streamlit, Vercel, BI notes
├── tools/regen_readme_images.py
├── requirements.txt
├── requirements-dev.txt
├── LICENSE
├── NOTICE.md
└── README.md
```

---

## Contributing

See [**CONTRIBUTING.md**](./CONTRIBUTING.md).

---

## Hero & diagram assets (HiDPI)

README diagrams are **PNGs**: they always fill the GitHub content column (`width="100%"`), but GitHub does not reflow text inside an image — the generator uses **larger fonts**, **word-wrapping**, and **extra height** so lines stay **inside** each card on phones. For a **truly responsive** layout (text that reflows with CSS), open the **`static-site/`** landing page or the **Streamlit** app. **PNG** is what the README loads; the script also writes **WebP** beside it.

```bash
pip install pillow
python3 tools/regen_readme_images.py
```

Wrap README images in `<a href="./hero.png?v=…">` if you want taps on GitHub to open the file **on the current branch** (bare `<img>` links are often tied to the default branch). Bump `?v=` when you replace PNG bytes so the mobile app does not show a cached copy (this README uses `?v=6`). Vector: [`architecture.svg`](./architecture.svg).

---

## Legal — licence & disclaimer

### Software (this repository)

Copyright **© 2025 Thomas Gollogly**. The **source code and documentation** in this repository are licensed under the [**MIT License**](./LICENSE) — use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies, subject to the conditions in that file.

### Statistics and third‑party content

Official UK statistics accessed via configured URLs (e.g. **Office for National Statistics**) are **© Crown copyright** and made available under the [**Open Government Licence v3.0**](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). This project **does not** grant you rights in those statistics beyond what the publisher licences; you must **attribute** and comply with the **OGL** and any publisher terms. See [**NOTICE.md**](./NOTICE.md).

### No warranty / not advice

The **Software** and any **outputs** (figures, exports, dashboards) are provided **“as is”**, without warranty of any kind. They are **not** official ONS releases, **not** financial, investment, tax, or legal advice, and **not** a substitute for professional judgment or the **original** publications on [ons.gov.uk](https://www.ons.gov.uk/). **ONS revises** series; always check the publisher for authoritative figures.

### Trademarks

Names such as **DuckDB**, **Python**, **Streamlit**, **Vercel**, and others may be trademarks of their respective owners; this project is **not** endorsed by them unless stated.

---

<p align="center">
  <sub>README last structured for clarity on GitHub — coloured badges use <a href="https://shields.io">shields.io</a>. Inline HTML is limited by GitHub’s sanitizer; for custom themes use your own site or the Streamlit app.</sub>
</p>
