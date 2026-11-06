# uk-macro-analytics-engine

![Project hero](./hero.png)

A small, production-minded **Python 3.11+** pipeline that downloads **open UK macroeconomic**
CSVs, validates shape and column names, caches **Parquet** locally, loads into **DuckDB**,
and runs **vectorized SQL** analytics (rolling windows, year-over-year inflation, fiscal totals).

## Architecture

```mermaid
flowchart LR
  subgraph Ingest["Ingestion"]
    CFG["config.py\n(dataset URLs + DuckDB tuning)"]
    HTTP["requests\n(retries + timeouts)"]
    DF["data_fetcher.py\n(parse · validate · Parquet cache)"]
  end

  subgraph Store["Storage & compute"]
    DDB["DuckDB\n(db_engine.py)"]
    VWS["Views / indexes\n(v_cpih_core · v_psnb_monthly)"]
  end

  subgraph Analytics["Analytics & export"]
    AN["analytics.py\n(SQL + exports)"]
    OUT["data/exports\n(.parquet · .json)"]
  end

  CFG --> DF
  HTTP --> DF
  DF --> DDB
  DDB --> VWS
  VWS --> AN
  AN --> OUT
```

## Tech stack

| Layer | Choice |
|-------|--------|
| Language | Python **3.11+** (also tested on **3.12**) |
| Analytics / OLAP | **DuckDB** with indexes and pragmatic PRAGMAs |
| Tabular IO | **pandas** + **pyarrow** (Parquet) |
| HTTP | **requests** with retries |
| Testing | **pytest** |
| CI | **GitHub Actions** (audit → compile → tests) |
| Edge / Workers | No hard dependency on a specific host. Pure Python **stdlib + wheels**; for **Cloudflare Workers** use a **Python compat** or **container** pattern—this repo is CLI-first. |

## Project layout

```
.
├── .github/workflows/ci.yml
├── src/
│   ├── __init__.py
│   ├── config.py          # URLs, paths, DuckDB settings
│   ├── data_fetcher.py    # download + cache + validation
│   ├── db_engine.py       # DuckDB connect, views, indexes
│   ├── analytics.py       # queries + exports
│   └── security_audit.py  # lightweight static checks
├── tests/test_pipeline.py
├── requirements.txt
├── LICENSE
├── NOTICE.md
└── README.md
```

## Getting started

### Prerequisites

- **Python 3.11+**
- Network access for dataset downloads (or use your own Parquet by wiring a custom `DatasetSpec`).

### Install

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Quickstart (CLI)

**1) Fetch one dataset to the Parquet cache**

```bash
python -m src.data_fetcher ons_cpih_monthly
python -m src.data_fetcher ons_psnb_monthly
```

**2) Run the full analytics pipeline** (downloads if needed, loads DuckDB, prints previews, exports)

```bash
python -m src.analytics
```

Exports are written under `data/exports/`:

- `cpih_yoy.parquet` / `cpih_yoy.json`
- `psnb_monthly.parquet` / `psnb_monthly.json`

Use `--no-export` on `analytics` to skip writing files.

## Configuration

- **Dataset URLs and expected columns**: `src/config.py` (`DATASETS` mapping).
- **DuckDB tuning**: `DuckDBSettings` in the same file (`threads`, `memory_limit`, etc.).
- **Cache location**: `data/cache/parquet/` (created automatically).

If a publisher changes CSV layout, update the **`DatasetSpec`** or extend **`_alias_key_columns`** in `data_fetcher.py`.

## Security & compliance

- **Dependency hygiene**: requirements are **version-pinned** ranges; CI runs `src/security_audit.py` to flag **insecure `git+http`** deps and other risky patterns.
- **Secrets**: Do not commit API keys; the audit script flags common risky literals.
- **Legal — software**: This codebase is released under the **MIT License** (see `LICENSE`).
- **Legal — data**: UK public-sector datasets are often under the **Open Government Licence (OGL)**. See `NOTICE.md` and each publisher’s terms. This project does **not** grant rights to third-party data; you must attribute and comply with the relevant licence when redistributing **derived** statistics or charts.

## Continuous integration

Workflow: `.github/workflows/ci.yml`

1. `python src/security_audit.py`
2. `python -m compileall -q src tests`
3. `pytest -q --tb=short`

## Tests

```bash
pytest -q
```

## Hero image

The markdown above references `./hero.png`. Add your own dashboard screenshot or diagram at the repository root as **`hero.png`** (not committed in this template).

## Licence

Code: **MIT** — see `LICENSE`. Data: governed by publisher licences (see `NOTICE.md`).
