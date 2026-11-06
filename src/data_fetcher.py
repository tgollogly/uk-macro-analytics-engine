"""
Download open UK macroeconomic datasets with caching, retries, and schema guardrails.
"""

from __future__ import annotations

import logging
import time
import csv
from calendar import month_abbr
from io import BytesIO, TextIOWrapper
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd
import requests

from src.config import DatasetSpec, Settings, get_settings

logger = logging.getLogger(__name__)


class DataFetchError(RuntimeError):
    """Raised when download, parse, or validation fails."""


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _cache_path_for(spec: DatasetSpec, settings: Settings) -> Path:
    safe = "".join(c if c.isalnum() else "_" for c in spec.key)
    return settings.paths.parquet_dir / f"{safe}.parquet"


def _http_get_with_retries(
    url: str, settings: Settings, session: requests.Session | None = None
) -> bytes:
    sess = session or requests.Session()
    headers = settings.http.headers
    last_exc: Exception | None = None
    for attempt in range(1, settings.http.max_retries + 1):
        try:
            resp = sess.get(
                url,
                headers=headers,
                timeout=settings.http.timeout_seconds,
            )
            resp.raise_for_status()
            return resp.content
        except requests.RequestException as exc:
            last_exc = exc
            logger.warning(
                "HTTP GET attempt %s/%s failed for %s: %s",
                attempt,
                settings.http.max_retries,
                url,
                exc,
            )
            if attempt < settings.http.max_retries:
                time.sleep(0.5 * attempt)
    assert last_exc is not None
    raise DataFetchError(f"Failed to download after retries: {url}") from last_exc


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names to lowercase snake_case for stable downstream SQL."""
    out = df.copy()
    out.columns = [
        str(c).strip().lower().replace(" ", "_").replace("__", "_") for c in out.columns
    ]
    return out


def _alias_key_columns(df: pd.DataFrame, spec: DatasetSpec) -> pd.DataFrame:
    """
    Map publisher-specific column names onto canonical names used in analytics.

    Publishers revise CSV layouts; we accept a small set of synonyms per dataset.
    """
    out = df.copy()
    cols = set(out.columns)

    if spec.key in ("ons_cpih_monthly", "ons_psnb_monthly"):
        if "time" not in cols:
            for candidate in ("obs", "period", "month", "date"):
                if candidate in cols:
                    out = out.rename(columns={candidate: "time"})
                    cols = set(out.columns)
                    break
        if "value" not in cols:
            # Fiscal series may label the observation as amount / borrowing.
            for candidate in ("amount", "v", "data", "cpih", "index"):
                if candidate in cols:
                    out = out.rename(columns={candidate: "value"})
                    break

    return out


def _parse_ons_month_label(label: str) -> str | None:
    """
    Convert labels like '2025 JAN' to ISO date '2025-01-01' (month start).
    Annual rows like '1997' have no month and return None.
    """
    label = label.strip().strip('"')
    parts = label.split()
    if len(parts) != 2:
        return None
    year_s, mon_s = parts
    if not year_s.isdigit() or len(year_s) != 4:
        return None
    mon = mon_s[:3].upper()
    month_map = {m.upper(): i for i, m in enumerate(month_abbr) if m}
    if mon not in month_map:
        return None
    year = int(year_s)
    month = month_map[mon]
    return f"{year:04d}-{month:02d}-01"


def parse_ons_generator_monthly_csv(raw: bytes, series_key: str) -> pd.DataFrame:
    """
    Parse ONS 'generator' CSV exports into tidy monthly (time, value) rows.

    Skips preamble metadata rows until data rows look like 'YYYY MON','num'.
    """
    # utf-8-sig handles occasional BOM; ONS uses ASCII quotes mostly.
    text_stream = TextIOWrapper(BytesIO(raw), encoding="utf-8-sig", newline="")
    reader = csv.reader(text_stream)

    rows: list[tuple[str, float]] = []
    for cols in reader:
        if len(cols) != 2:
            continue
        period, val_s = cols[0].strip().strip('"'), cols[1].strip().strip('"')
        iso = _parse_ons_month_label(period)
        if iso is None:
            continue
        if val_s == "" or val_s is None:
            continue
        try:
            val = float(val_s)
        except ValueError:
            continue
        rows.append((iso, val))

    if not rows:
        raise DataFetchError(f"No monthly rows parsed from ONS CSV for {series_key}")

    df = pd.DataFrame(rows, columns=["time", "value"])
    # Sort chronologically for window functions downstream
    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    df = df.dropna(subset=["time"]).sort_values("time")
    df["time"] = df["time"].dt.strftime("%Y-%m-%d")
    return df


def _validate_schema(df: pd.DataFrame, spec: DatasetSpec) -> None:
    expected = [c.lower().replace(" ", "_") for c in spec.expected_columns]
    missing = [c for c in expected if c not in df.columns]
    if missing:
        raise DataFetchError(
            f"Schema validation failed for {spec.key}: missing columns {missing}; "
            f"got {list(df.columns)}"
        )


def fetch_dataset_to_parquet(
    dataset_key: str,
    settings: Settings | None = None,
    *,
    force_refresh: bool = False,
    session: requests.Session | None = None,
) -> Path:
    """
    Download a configured dataset, validate columns, cache as Parquet, return path.

    Raises DataFetchError on network, parsing, or schema errors.
    """
    settings = settings or get_settings()
    if dataset_key not in settings.datasets:
        raise DataFetchError(f"Unknown dataset key: {dataset_key}")
    spec = settings.datasets[dataset_key]

    cache_file = _cache_path_for(spec, settings)
    _ensure_dir(cache_file.parent)

    if cache_file.exists() and not force_refresh:
        logger.info("Using cached Parquet: %s", cache_file)
        return cache_file

    raw = _http_get_with_retries(spec.url, settings, session=session)

    if spec.key in ("ons_cpih_monthly", "ons_psnb_monthly"):
        try:
            df = parse_ons_generator_monthly_csv(raw, spec.key)
        except Exception as exc:
            raise DataFetchError(f"Could not parse ONS series CSV for {spec.key}") from exc
    else:
        try:
            df = pd.read_csv(BytesIO(raw))
        except Exception as exc:
            raise DataFetchError(f"Could not parse CSV for {spec.key}") from exc

    df = _normalize_columns(df)
    df = _alias_key_columns(df, spec)
    _validate_schema(df, spec)

    try:
        df.to_parquet(cache_file, index=False, engine="pyarrow")
    except Exception as exc:
        raise DataFetchError(f"Failed to write Parquet for {spec.key}") from exc

    logger.info("Cached dataset %s to %s", dataset_key, cache_file)
    return cache_file


def load_parquet_into_relation(
    con: duckdb.DuckDBPyConnection,
    parquet_path: Path,
    table_name: str,
) -> None:
    """Register a Parquet file as a DuckDB table."""
    con.execute(
        f"""
        CREATE OR REPLACE TABLE {table_name} AS
        SELECT * FROM read_parquet(?);
        """,
        [str(parquet_path)],
    )


def fetch_and_register(
    dataset_key: str,
    con: duckdb.DuckDBPyConnection,
    table_name: str,
    settings: Settings | None = None,
    *,
    force_refresh: bool = False,
    session: requests.Session | None = None,
) -> Path:
    """
    End-to-end: fetch dataset, validate, cache Parquet, load into DuckDB table.
    """
    path = fetch_dataset_to_parquet(
        dataset_key, settings=settings, force_refresh=force_refresh, session=session
    )
    load_parquet_into_relation(con, path, table_name)
    return path


# ---- CLI -----------------------------------------------------------------

def _parse_args(argv: list[str] | None = None) -> Any:
    import argparse

    p = argparse.ArgumentParser(description="Fetch UK macro datasets to local Parquet cache.")
    p.add_argument(
        "dataset",
        nargs="?",
        default="ons_cpih_monthly",
        help="Dataset key from config (default: ons_cpih_monthly)",
    )
    p.add_argument("--refresh", action="store_true", help="Ignore cache and re-download")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = _parse_args(argv)
    settings = get_settings()
    path = fetch_dataset_to_parquet(
        args.dataset, settings=settings, force_refresh=args.refresh
    )
    print(path)


if __name__ == "__main__":
    main()
