# Changelog

All notable releases of this repository are documented here.

## [0.1.0] — 2026-11-17

First sealed GitHub Release of the UK Macro Analytics Engine portfolio pipeline.

- **Pipeline** — ONS CSV ingest, validation, Parquet cache, DuckDB views, and SQL analytics (`src/`, Streamlit dashboard, export tools).
- **Static hub** — `static-site/` landing, demo JSON, case-study summaries, optional Cloudflare Workers (`workers/`).
- **CI** — Ruff, pytest (3.11/3.12), `security_audit.py`, pip-audit, and ATS API worker typecheck/tests; npm override for patched `picomatch`.
- **Release** — Tag-triggered GitHub Release with Python sdist/wheel, ATS worker npm pack tarball, source zip, `SHA256SUMS.txt`, and build provenance attestations.