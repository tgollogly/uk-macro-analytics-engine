"""
Vectorized macro analytics on DuckDB: rolling windows, YoY, fiscal aggregates, exports.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import duckdb

from src.config import get_settings
from src.db_engine import export_dir, setup_database

logger = logging.getLogger(__name__)


def cpih_rolling_and_yoy(con: duckdb.DuckDBPyConnection) -> duckdb.DuckDBPyRelation:
    """
    CPIH: 3-month rolling average of index level and year-over-year % change.
    """
    return con.sql(
        """
        WITH ordered AS (
          SELECT
            obs_date,
            index_level,
            AVG(index_level) OVER (
              ORDER BY obs_date
              ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
            ) AS cpih_3m_avg
          FROM v_cpih_core
          WHERE obs_date IS NOT NULL AND index_level IS NOT NULL
        ),
        yoy AS (
          SELECT
            obs_date,
            index_level,
            cpih_3m_avg,
            LAG(index_level, 12) OVER (ORDER BY obs_date) AS index_12m_ago,
            CASE
              WHEN LAG(index_level, 12) OVER (ORDER BY obs_date) IS NULL
                   OR LAG(index_level, 12) OVER (ORDER BY obs_date) = 0
              THEN NULL
              ELSE
                100.0 * (index_level - LAG(index_level, 12) OVER (ORDER BY obs_date))
                / LAG(index_level, 12) OVER (ORDER BY obs_date)
            END AS yoy_pct
          FROM ordered
        )
        SELECT * FROM yoy ORDER BY obs_date;
        """
    )


def fiscal_monthly_totals(con: duckdb.DuckDBPyConnection) -> duckdb.DuckDBPyRelation:
    """Public sector net borrowing (ex. public sector banks): monthly series in £m (ONS DZLS)."""
    return con.sql(
        """
        SELECT
          obs_date,
          SUM(net_borrowing_gbp_m) AS total_net_borrowing_gbp_m,
          COUNT(*) AS row_count
        FROM v_psnb_monthly
        WHERE obs_date IS NOT NULL AND net_borrowing_gbp_m IS NOT NULL
        GROUP BY 1
        ORDER BY 1;
        """
    )


def print_preview(relation: duckdb.DuckDBPyRelation, limit: int = 8) -> None:
    df = relation.df()
    print(df.head(limit).to_string(index=False))


def export_relation_parquet(relation: duckdb.DuckDBPyRelation, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    relation.write_parquet(str(path))


def export_relation_json_records(relation: duckdb.DuckDBPyRelation, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df = relation.df()
    records: list[dict[str, Any]] = df.to_dict(orient="records")
    path.write_text(json.dumps(records, indent=2, default=str), encoding="utf-8")


def export_relation_csv(relation: duckdb.DuckDBPyRelation, path: Path) -> None:
    """Write query results as UTF-8 CSV (Power BI / Excel / SSMS import friendly)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df = relation.df()
    df.to_csv(path, index=False, encoding="utf-8")


def run_analytics(
    con: duckdb.DuckDBPyConnection,
    *,
    export_outputs: bool = True,
) -> dict[str, Path | None]:
    """
    Run standard analytics; optionally write Parquet + JSON to data/exports/.
    Returns paths written.
    """
    setup_database(con, with_indexes=True)

    out: dict[str, Path | None] = {}
    base = export_dir()

    cpih_rel = cpih_rolling_and_yoy(con)
    print("=== CPIH rolling & YoY (preview) ===")
    print_preview(cpih_rel)

    psnb_rel = fiscal_monthly_totals(con)
    print("=== PSNB monthly series (preview) ===")
    print_preview(psnb_rel)

    if export_outputs:
        p1 = base / "cpih_yoy.parquet"
        p2 = base / "cpih_yoy.json"
        p3 = base / "psnb_monthly.parquet"
        p4 = base / "psnb_monthly.json"
        c1 = base / "cpih_yoy.csv"
        c2 = base / "psnb_monthly.csv"
        export_relation_parquet(cpih_rel, p1)
        export_relation_json_records(cpih_rel, p2)
        export_relation_csv(cpih_rel, c1)
        export_relation_parquet(psnb_rel, p3)
        export_relation_json_records(psnb_rel, p4)
        export_relation_csv(psnb_rel, c2)
        out.update(
            {
                "cpih_parquet": p1,
                "cpih_json": p2,
                "cpih_csv": c1,
                "psnb_parquet": p3,
                "psnb_json": p4,
                "psnb_csv": c2,
            }
        )
    else:
        keys = (
            "cpih_parquet",
            "cpih_json",
            "cpih_csv",
            "psnb_parquet",
            "psnb_json",
            "psnb_csv",
        )
        out = {k: None for k in keys}

    return out


def _parse_args(argv: list[str] | None = None) -> Any:
    import argparse

    p = argparse.ArgumentParser(description="Run UK macro analytics on DuckDB.")
    p.add_argument("--no-export", action="store_true", help="Skip Parquet/JSON export")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    from src.data_fetcher import fetch_and_register
    from src.db_engine import connect_duckdb

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = _parse_args(argv)
    settings = get_settings()
    con = connect_duckdb(settings)
    try:
        fetch_and_register("ons_cpih_monthly", con, "ons_cpih_monthly", settings)
        fetch_and_register("ons_psnb_monthly", con, "ons_psnb_monthly", settings)
        run_analytics(con, export_outputs=not args.no_export)
    finally:
        con.close()


if __name__ == "__main__":
    main()
