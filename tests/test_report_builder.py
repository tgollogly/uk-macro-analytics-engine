"""Smoke tests for static HTML report builder."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.report_builder import build_report


def test_build_report_writes_html(tmp_path: Path) -> None:
    exp = tmp_path / "exports"
    exp.mkdir(parents=True)
    cpih = pd.DataFrame(
        {
            "obs_date": pd.to_datetime(["2024-01-01", "2024-02-01", "2025-02-01"]),
            "yoy_pct": [None, 2.0, 3.0],
        }
    )
    psnb = pd.DataFrame(
        {
            "obs_date": pd.to_datetime(["2025-01-01"]),
            "total_net_borrowing_gbp_m": [10.0],
        }
    )
    cpih.to_parquet(exp / "cpih_yoy.parquet", index=False)
    psnb.to_parquet(exp / "psnb_monthly.parquet", index=False)

    out = tmp_path / "report.html"
    build_report(out, base=exp)
    text = out.read_text(encoding="utf-8")
    assert "UK macro" in text
    assert "Chart" in text or "chart" in text
    assert "const series" in text
