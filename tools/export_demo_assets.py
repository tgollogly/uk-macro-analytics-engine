#!/usr/bin/env python3
"""
Write static-site/demo/*.json + manifest.json from the **same** analytics exports as the Python pipeline.

Preferred (real ONS pull): run without --from-exports — fetches CSVs, runs DuckDB analytics, writes
data/exports/*.csv then copies **valid JSON** into static-site/demo/.

CI / offline: pass --from-exports to build from existing data/exports/*.csv (must exist).

Does not invent data: fails if exports are missing or fetch fails (unless --from-exports with files).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DEMO = ROOT / "static-site" / "demo"


def _finite_or_none(x: object) -> float | None:
    if x is None:
        return None
    if isinstance(x, float) and not math.isfinite(x):
        return None
    if isinstance(x, str) and x.strip() == "":
        return None
    return float(x)  # type: ignore[arg-type]


def _row_cpih(r: dict[str, str | None]) -> dict[str, object]:
    od = r.get("obs_date") or ""
    return {
        "obs_date": str(od)[:10],
        "index_level": _finite_or_none(r.get("index_level")),  # type: ignore[arg-type]
        "cpih_3m_avg": _finite_or_none(r.get("cpih_3m_avg")),  # type: ignore[arg-type]
        "index_12m_ago": _finite_or_none(r.get("index_12m_ago")),  # type: ignore[arg-type]
        "yoy_pct": _finite_or_none(r.get("yoy_pct")),  # type: ignore[arg-type]
    }


def _row_psnb(r: dict[str, str | None]) -> dict[str, object]:
    od = r.get("obs_date") or ""
    return {
        "obs_date": str(od)[:10],
        "total_net_borrowing_gbp_m": _finite_or_none(r.get("total_net_borrowing_gbp_m")),  # type: ignore[arg-type]
        "row_count": int(float(r["row_count"])) if r.get("row_count") not in (None, "") else None,
    }


def _read_csv_rows(path: Path) -> list[dict[str, str | None]]:
    import csv

    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _run_pipeline_exports() -> None:
    from src.analytics import run_analytics
    from src.config import get_settings
    from src.data_fetcher import DataFetchError, fetch_and_register
    from src.db_engine import connect_duckdb

    settings = get_settings()
    con = connect_duckdb(settings)
    try:
        try:
            fetch_and_register(
                "ons_cpih_monthly",
                con,
                "ons_cpih_monthly",
                settings,
                force_refresh=True,
            )
            fetch_and_register(
                "ons_psnb_monthly",
                con,
                "ons_psnb_monthly",
                settings,
                force_refresh=True,
            )
        except DataFetchError as exc:
            print(f"ERROR: ONS fetch failed (network or URL): {exc}", file=sys.stderr)
            print("Use --from-exports only when data/exports/*.csv already exists.", file=sys.stderr)
            raise SystemExit(2) from exc
        run_analytics(con, export_outputs=True)
    finally:
        con.close()


def main() -> int:
    p = argparse.ArgumentParser(description="Export demo JSON for static-site/demo")
    p.add_argument(
        "--from-exports",
        action="store_true",
        help="Read existing data/exports/*.csv (no network); fails if files missing",
    )
    p.add_argument(
        "--demo-dir",
        type=Path,
        default=None,
        help=f"Output directory (default: {DEFAULT_DEMO})",
    )
    args = p.parse_args()
    demo_dir = args.demo_dir or DEFAULT_DEMO

    export_dir = ROOT / "data" / "exports"
    cpih_csv = export_dir / "cpih_yoy.csv"
    psnb_csv = export_dir / "psnb_monthly.csv"

    if not args.from_exports:
        _run_pipeline_exports()
    else:
        if not cpih_csv.is_file() or not psnb_csv.is_file():
            print("ERROR: data/exports/cpih_yoy.csv and psnb_monthly.csv required", file=sys.stderr)
            return 1

    cpih_rows = [_row_cpih(row) for row in _read_csv_rows(cpih_csv)]
    psnb_rows = [_row_psnb(row) for row in _read_csv_rows(psnb_csv)]
    generated_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    manifest = {
        "generated_at_utc": generated_at,
        "pipeline": "uk-macro-analytics-engine",
        "sources": {
            "cpih": {
                "series": "ONS CPIH all items (L522)",
                "config_url": (
                    "https://www.ons.gov.uk/generator?"
                    "format=csv&uri=/economy/inflationandpriceindices/timeseries/l522/mm23"
                ),
                "rows": len(cpih_rows),
                "export_csv": "data/exports/cpih_yoy.csv",
            },
            "psnb": {
                "series": "ONS PSNB ex banks, monthly £m (DZLS)",
                "config_url": (
                    "https://www.ons.gov.uk/generator?"
                    "format=csv&uri=/economy/governmentpublicsectorandtaxes/publicsectorfinance"
                    "/timeseries/dzls/pusf"
                ),
                "rows": len(psnb_rows),
                "export_csv": "data/exports/psnb_monthly.csv",
            },
        },
        "limitations": [
            "ONS may revise past periods; confirm headline figures on ons.gov.uk.",
            "CPIH YoY is null for the first ~11 months and whenever the lag index is missing.",
            "PSNB row_count > 1 means multiple CSV rows were summed for that month.",
            "This bundle is a snapshot at generated_at_utc — not a live feed.",
        ],
    }

    _write_json(demo_dir / "cpih_yoy.json", cpih_rows)
    _write_json(demo_dir / "psnb_monthly.json", psnb_rows)
    _write_json(demo_dir / "manifest.json", manifest)
    print(f"Wrote {demo_dir}/cpih_yoy.json ({len(cpih_rows)} rows)")
    print(f"Wrote {demo_dir}/psnb_monthly.json ({len(psnb_rows)} rows)")
    print(f"Wrote {demo_dir}/manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
