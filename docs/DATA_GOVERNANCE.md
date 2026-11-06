# Data governance (portfolio / interview notes)

This repo is a **small batch analytics pipeline**, not an enterprise data platform. These notes show how you would **talk about governance** in an interview using what is actually implemented here.

## Data lineage

| Stage | What happens | Artifact |
|-------|----------------|----------|
| Source | Configured HTTPS GET of open ONS CSVs | `src/config.py` (`DatasetSpec.url`) |
| Ingest | Parse, validate columns, cache | `data/cache/parquet/*.parquet` |
| Transform | Load into DuckDB, views, SQL analytics | In-memory or file DB |
| Publish | Parquet, JSON, CSV for tools | `data/exports/` |

## Data quality

- **Schema validation**: Expected columns per dataset; ingestion fails fast with a clear error (`DataFetchError`).
- **Parser guardrails**: ONS generator CSVs mix annual and monthly rows; only `YYYY MON` rows are kept for monthly series.
- **Reconciliation (manual)**: Compare latest index level against the ONS website for the same series ID if a number looks wrong.

## Ownership and licences

- **Publisher**: Office for National Statistics (ONS) for the default series. You are responsible for **OGL** attribution when republishing charts (see `NOTICE.md`).
- **This repository**: Code is MIT; **third-party statistics are not redistributed** except as your own derived exports when you run the pipeline locally.

## Retention

- **Cache and exports** are local and listed in `.gitignore`. CI does not persist long-term data.
- Refresh policy: re-run fetch with `--refresh` when you need the latest ONS revision.

## Security

- No credentials in repo; `src/security_audit.py` runs in CI.
- Dependencies are pinned in `requirements.txt`.

## SQL Server / Power BI alignment (free tier)

- **CSV** exports (`*.csv` in `data/exports/`) import cleanly into **SQL Server** (staging table) or **Power BI Desktop** (Get Data → Text/CSV).
- DuckDB SQL is **ANSI-like**; the same logic can be rewritten in T-SQL for interviews—see `docs/SQL_SERVER_MAPPING.md`.
