"""
DuckDB engine: connection lifecycle, performance pragmas, schema, and indexes.
"""

from __future__ import annotations

import logging
from pathlib import Path

import duckdb

from src.config import Settings, get_settings

logger = logging.getLogger(__name__)


def connect_duckdb(settings: Settings | None = None) -> duckdb.DuckDBPyConnection:
    """
    Open a DuckDB connection (in-memory or persistent) and apply performance settings.

    The returned connection should be closed by the caller when done, or use as context.
    """
    settings = settings or get_settings()
    db_path = settings.paths.duckdb_path or ":memory:"
    logger.info("Opening DuckDB at %s", db_path)

    con = duckdb.connect(database=db_path)

    # Thread and memory limits for predictable resource use on CI and laptops.
    con.execute(f"PRAGMA threads={int(settings.duckdb.threads)};")
    con.execute(f"PRAGMA memory_limit='{settings.duckdb.memory_limit}';")

    if settings.duckdb.enable_object_cache:
        con.execute("PRAGMA enable_object_cache=true;")
    if not settings.duckdb.preserve_insertion_order:
        con.execute("PRAGMA preserve_insertion_order=false;")

    return con


def ensure_macro_schema(con: duckdb.DuckDBPyConnection) -> None:
    """
    Create analytic helper views / tables expected by the analytics module.

    Base tables are populated from Parquet by data_fetcher.load_parquet_into_relation.
    """
    # Rolling window prep: ensure time is typed where present.
    con.execute(
        """
        CREATE OR REPLACE VIEW v_cpih_core AS
        SELECT
          TRY_CAST(time AS DATE) AS obs_date,
          TRY_CAST(value AS DOUBLE) AS index_level
        FROM ons_cpih_monthly
        WHERE time IS NOT NULL;
        """
    )

    con.execute(
        """
        CREATE OR REPLACE VIEW v_psnb_monthly AS
        SELECT
          TRY_CAST(time AS DATE) AS obs_date,
          TRY_CAST(value AS DOUBLE) AS net_borrowing_gbp_m
        FROM ons_psnb_monthly
        WHERE time IS NOT NULL;
        """
    )


def create_indexes(con: duckdb.DuckDBPyConnection) -> None:
    """Create indexes on hot join/filter columns for faster scans."""
    # DuckDB ART indexes on expressions used in WHERE/GROUP BY.
    for ddl in (
        "CREATE INDEX IF NOT EXISTS idx_cpih_date ON ons_cpih_monthly(time);",
        "CREATE INDEX IF NOT EXISTS idx_psnb_date ON ons_psnb_monthly(time);",
    ):
        try:
            con.execute(ddl)
        except Exception as exc:
            # DuckDB may not create the index if unsupported for a storage engine; log only.
            logger.warning("Index creation skipped or failed (%s): %s", ddl, exc)


def setup_database(
    con: duckdb.DuckDBPyConnection,
    *,
    with_indexes: bool = True,
) -> None:
    """Full schema setup after raw tables exist."""
    ensure_macro_schema(con)
    if with_indexes:
        create_indexes(con)


def export_dir(settings: Settings | None = None) -> Path:
    settings = settings or get_settings()
    path = settings.paths.export_dir
    path.mkdir(parents=True, exist_ok=True)
    return path

