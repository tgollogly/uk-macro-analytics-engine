"""Regression tests for rebuilt NI prescribing and UK energy trade summaries."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SUMMARY_DIR = ROOT / "static-site" / "case-studies"
NI_FIXTURE = ROOT / "tests" / "fixtures" / "ni_prescribing_aug2026_sample.csv"
ONS_XLSX = ROOT / "data" / "cache" / "case-studies" / "tradepublicationtables2026aug.xlsx"


@pytest.fixture
def ni_summary() -> dict:
    path = SUMMARY_DIR / "ni-prescribing-2026-08-summary.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def energy_summary() -> dict:
    path = SUMMARY_DIR / "uk-energy-trade-q2-2026-summary.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_committed_ni_totals_match_pipeline(ni_summary: dict) -> None:
    from src.case_studies.prescribing import aggregate_ni_gp_prescribing

    full_csv = ROOT / "data" / "cache" / "case-studies" / "ni-gp-prescribing-2026-08.csv"
    if not full_csv.is_file():
        pytest.skip("full NI CSV not in cache (local/CI optional)")
    live = aggregate_ni_gp_prescribing(full_csv)
    assert live.detail_rows == ni_summary["detail_rows"]
    assert live.total_items == ni_summary["total_items"]
    assert live.distinct_practices == ni_summary["distinct_practices"]
    assert live.actual_cost_gbp == pytest.approx(ni_summary["actual_cost_gbp"], rel=1e-6)
    assert live.tirzepatide_items == ni_summary["tirzepatide_items"]
    assert live.atorvastatin_items == ni_summary["atorvastatin_items"]


def test_ni_fixture_control_totals() -> None:
    from src.case_studies.prescribing import aggregate_ni_gp_prescribing

    s = aggregate_ni_gp_prescribing(NI_FIXTURE)
    assert s.detail_rows == 200
    assert s.distinct_practices == 1
    assert s.total_items == 549
    assert s.actual_cost_gbp == pytest.approx(22263.63, abs=0.01)


def test_committed_energy_fuel_exports_qoq(energy_summary: dict) -> None:
    exp = energy_summary["fuels_exports_world"]
    assert exp["q1_2026_gbp_m"] == 7.819
    assert exp["q2_2026_gbp_m"] == 14.276
    assert exp["qoq_change_pct"] == pytest.approx(82.6, abs=0.1)
    assert exp["qoq_change_gbp_m"] == pytest.approx(6.5, abs=0.1)


def test_energy_xlsx_parser_matches_json(energy_summary: dict) -> None:
    if not ONS_XLSX.is_file():
        pytest.skip("ONS xlsx not in cache")
    from src.case_studies.energy_trade import parse_quarterly_cp_xlsx

    parsed = parse_quarterly_cp_xlsx(ONS_XLSX)
    assert parsed.fuels_exports_world.q2_2026_gbp_m == pytest.approx(
        energy_summary["fuels_exports_world"]["q2_2026_gbp_m"], abs=0.001
    )
    assert parsed.fuels_imports_world.qoq_change_pct == pytest.approx(
        energy_summary["fuels_imports_world"]["qoq_change_pct"], abs=0.1
    )


def test_case_studies_manifest_hashes(ni_summary: dict, energy_summary: dict) -> None:
    manifest = json.loads((SUMMARY_DIR / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["sources"]["ni_prescribing"]["sha256"] == ni_summary["sha256_source_csv"]
    assert manifest["sources"]["ons_trade_tables"]["sha256"] == energy_summary["sha256_source_xlsx"]
    assert "rebuild_label" in manifest
