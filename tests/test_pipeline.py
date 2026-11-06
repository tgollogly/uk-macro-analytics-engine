"""
Pytest coverage: data fetch + validation, DuckDB loading, analytics, security audit.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import duckdb
import pandas as pd
import pytest

from src import data_fetcher
from src.analytics import cpih_rolling_and_yoy, fiscal_monthly_totals, run_analytics
from src.config import DatasetSpec, Paths, Settings
from src.data_fetcher import (
    fetch_dataset_to_parquet,
    load_parquet_into_relation,
    parse_ons_generator_monthly_csv,
)
from src.db_engine import connect_duckdb, setup_database
from src.security_audit import scan_repo


def _minimal_settings(tmp_path: Path) -> Settings:
    ds = {
        "ons_cpih_monthly": DatasetSpec(
            key="ons_cpih_monthly",
            description="test",
            url="https://example.com/l522.csv",
            expected_columns=("time", "value"),
            date_column="time",
            value_columns=("value",),
        ),
        "ons_psnb_monthly": DatasetSpec(
            key="ons_psnb_monthly",
            description="test",
            url="https://example.com/dzls.csv",
            expected_columns=("time", "value"),
            date_column="time",
            value_columns=("value",),
        ),
    }
    return Settings(
        paths=Paths(project_root=tmp_path, duckdb_path=":memory:"),
        datasets=ds,
    )


def test_fetch_and_schema_validation(tmp_path: Path) -> None:
    settings = _minimal_settings(tmp_path)
    ons_csv = (
        '"Title","test"\n'
        '"2023 JAN","100.0"\n'
        '"2023 FEB","101.0"\n'
        '"2023 MAR","102.0"\n'
    )

    def fake_get(url: str, *args: object, **kwargs: object) -> bytes:
        if "l522" in url:
            return ons_csv.encode("utf-8")
        raise AssertionError(f"unexpected url {url}")

    with patch.object(data_fetcher, "_http_get_with_retries", side_effect=fake_get):
        path = fetch_dataset_to_parquet(
            "ons_cpih_monthly", settings=settings, force_refresh=True
        )
    assert path.exists()
    df = pd.read_parquet(path)
    assert list(df.columns) == ["time", "value"]
    assert len(df) == 3


def test_ons_parser_skips_annual_and_preamble() -> None:
    raw = (
        b'"Title","CPIH"\n'
        b'"1997","70.0"\n'
        b'"2023 JAN","100.0"\n'
        b'"2023 FEB","101.0"\n'
    )
    df = parse_ons_generator_monthly_csv(raw, "ons_cpih_monthly")
    assert list(df.columns) == ["time", "value"]
    assert len(df) == 2
    assert df.iloc[0]["time"].startswith("2023-")


def test_duckdb_pipeline_and_analytics(tmp_path: Path) -> None:
    settings = _minimal_settings(tmp_path)
    # 13+ months of CPIH for YoY leg (ONS monthly labels)
    lines: list[str] = ['"Title","CPIH"']
    months = [
        "JAN",
        "FEB",
        "MAR",
        "APR",
        "MAY",
        "JUN",
        "JUL",
        "AUG",
        "SEP",
        "OCT",
        "NOV",
        "DEC",
    ]
    for mi, mon in enumerate(months, start=1):
        lines.append(f'"2022 {mon}","{100.0 + mi}"')
    for mi, mon in enumerate(months, start=1):
        lines.append(f'"2023 {mon}","{100.0 + mi}"')
    ons_csv = "\n".join(lines) + "\n"
    psnb_csv = (
        '"Title","PSNB"\n'
        '"2023 JAN","15.0"\n'
        '"2023 FEB","11.0"\n'
    )

    def fake_get(url: str, *args: object, **kwargs: object) -> bytes:
        if "l522" in url:
            return ons_csv.encode("utf-8")
        if "dzls" in url:
            return psnb_csv.encode("utf-8")
        raise AssertionError(url)

    with patch.object(data_fetcher, "_http_get_with_retries", side_effect=fake_get):
        p1 = fetch_dataset_to_parquet("ons_cpih_monthly", settings=settings, force_refresh=True)
        p2 = fetch_dataset_to_parquet("ons_psnb_monthly", settings=settings, force_refresh=True)

    con = connect_duckdb(settings)
    try:
        load_parquet_into_relation(con, p1, "ons_cpih_monthly")
        load_parquet_into_relation(con, p2, "ons_psnb_monthly")
        setup_database(con)

        cpih_df = cpih_rolling_and_yoy(con).df()
        assert "yoy_pct" in cpih_df.columns
        # Last row should have YoY computed (non-null) once 12 months exist in 2023 series
        tail = cpih_df.dropna(subset=["yoy_pct"]).tail(1)
        assert not tail.empty

        psnb_df = fiscal_monthly_totals(con).df()
        assert len(psnb_df) == 2
        assert psnb_df.iloc[0]["total_net_borrowing_gbp_m"] == pytest.approx(15.0)

        exports = run_analytics(con, export_outputs=True)
        for k in ("cpih_parquet", "cpih_json", "cpih_csv", "psnb_parquet", "psnb_json", "psnb_csv"):
            p = exports.get(k)
            assert p is not None and Path(p).exists()
        with open(exports["cpih_json"], encoding="utf-8") as f:
            js = json.load(f)
        assert isinstance(js, list) and len(js) >= 1
        with open(exports["cpih_csv"], encoding="utf-8") as f:
            header = f.readline()
            assert "obs_date" in header
    finally:
        con.close()


def test_schema_guard_raises_on_bad_csv(tmp_path: Path) -> None:
    settings = _minimal_settings(tmp_path)
    bad_csv = "foo,bar\n1,2\n"

    def fake_get(url: str, *args: object, **kwargs: object) -> bytes:
        return bad_csv.encode("utf-8")

    with patch.object(data_fetcher, "_http_get_with_retries", side_effect=fake_get):
        with pytest.raises(data_fetcher.DataFetchError):
            fetch_dataset_to_parquet("ons_cpih_monthly", settings=settings, force_refresh=True)


def test_security_audit_no_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Point scanner at tmp_path with minimal package copy is heavy; scan real repo root
    root = Path(__file__).resolve().parent.parent
    res = scan_repo(root)
    errors = [f for f in res.findings if f.severity == "error"]
    assert errors == [], [e.message for e in errors]


def test_sql_invalid_table_raises() -> None:
    con = duckdb.connect(database=":memory:")
    try:
        with pytest.raises(duckdb.CatalogException):
            con.execute("SELECT * FROM nonexistent_table_xyz")
    finally:
        con.close()
