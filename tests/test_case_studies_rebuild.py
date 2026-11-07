"""Regression tests for rebuilt NI prescribing and UK energy trade summaries."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.case_studies.prescribing import (
    aggregate_ni_gp_prescribing,
    ni_prescribing_sanity_checks,
)

ROOT = Path(__file__).resolve().parent.parent
SUMMARY_DIR = ROOT / "static-site" / "case-studies"
NI_FIXTURE = ROOT / "tests/fixtures/ni_prescribing_aug2026_sample.csv"
NI_FULL = ROOT / "data/cache/case-studies/ni-gp-prescribing-2026-08.csv"
CPA08 = ROOT / "data/cache/case-studies/cpapublicationq22026august.xlsx"
ONS_XLSX = ROOT / "data/cache/case-studies/tradepublicationtables2026aug.xlsx"
EXPECTED_PERIOD = {"year_min": 2026, "year_max": 2026, "month_min": 8, "month_max": 8}


@pytest.fixture
def ni_summary() -> dict:
    path = SUMMARY_DIR / "ni-prescribing-2026-08-summary.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def energy_summary() -> dict:
    path = SUMMARY_DIR / "uk-energy-trade-q2-2026-summary.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_ni_fixture_sanity_not_json_mirror() -> None:
    sanity = ni_prescribing_sanity_checks(NI_FIXTURE)
    agg = aggregate_ni_gp_prescribing(NI_FIXTURE)
    assert sanity["detail_rows"] == agg.detail_rows == 200
    assert sanity["total_items"] == agg.total_items
    assert sanity["sum_actual_cost_gbp"] == pytest.approx(agg.actual_cost_gbp, abs=0.02)
    assert sanity["sum_gross_cost_gbp"] >= sanity["sum_actual_cost_gbp"]
    assert sanity["total_quantity"] > sanity["total_items"]


def test_ni_full_file_recompute_when_cached(ni_summary: dict) -> None:
    if not NI_FULL.is_file():
        pytest.skip("full NI CSV not in cache (CI optional)")
    sanity = ni_prescribing_sanity_checks(NI_FULL)
    assert sanity["detail_rows"] > 400_000
    for key, val in EXPECTED_PERIOD.items():
        assert sanity[key] == val, f"period check {key}"
    live = aggregate_ni_gp_prescribing(NI_FULL)
    assert live.detail_rows == sanity["detail_rows"]
    assert live.total_items == sanity["total_items"]
    assert live.actual_cost_gbp == pytest.approx(sanity["sum_actual_cost_gbp"], rel=1e-9)
    assert live.period_label == "2026-08"
    assert live.distinct_practices == sanity["distinct_practices"]
    assert sanity["rows_actual_gt_gross"] < sanity["detail_rows"] * 0.01


@pytest.mark.skipif(not NI_FULL.is_file(), reason="full NI CSV not cached")
def test_ni_committed_json_matches_full_recompute(ni_summary: dict) -> None:
    from src.case_studies.prescribing import aggregate_ni_gp_prescribing

    live = aggregate_ni_gp_prescribing(NI_FULL)
    assert live.total_items == ni_summary["total_items"]
    assert live.tirzepatide_items == ni_summary["tirzepatide_items"]
    assert ni_summary["sha256_source_csv"] == json.loads(
        (SUMMARY_DIR / "manifest.json").read_text(encoding="utf-8")
    )["sources"]["ni_prescribing"]["sha256"]


def test_cpa08_crude_yoy_from_xlsx() -> None:
    if not CPA08.is_file() or not ONS_XLSX.is_file():
        pytest.skip("CPA08 / trade tables not in cache")
    from src.case_studies.energy_trade import parse_cpa08_energy_trade

    parsed = parse_cpa08_energy_trade(CPA08, trade_tables_path=ONS_XLSX)
    crude = parsed.cpa_crude_exports
    assert crude.prior_q_gbp_b == pytest.approx(2.421, abs=0.01)
    assert crude.current_q_gbp_b == pytest.approx(7.271, abs=0.01)
    assert crude.yoy_change_pct == pytest.approx(200.3, abs=0.5)
    imp = parsed.cpa_crude_gas_imports
    assert imp.current_q_gbp_b == pytest.approx(11.680, abs=0.02)
    assert imp.yoy_change_pct == pytest.approx(36.6, abs=0.3)


def test_energy_basket_consistent_import_growth(energy_summary: dict) -> None:
    growth = energy_summary["cpa_energy_import_growth"]
    bal = energy_summary["cpa_energy_trade_balance"]
    assert "06" in growth["basket_definition"] and "19.2" in growth["basket_definition"]
    assert "06" in bal["basket_definition"]
    assert growth["share_of_goods_import_growth_pct"] == pytest.approx(44.2, abs=0.3)
    checks = energy_summary["original_pdf_claim_check"]
    energy_claim = next(c for c in checks if "44%" in c["claim"])
    assert energy_claim["validation"] == "close_on_basket"
    assert energy_claim["recomputed_share_pct"] == pytest.approx(44.2, abs=0.3)


def test_energy_json_has_workbook_claim_map(energy_summary: dict) -> None:
    checks = energy_summary["original_pdf_claim_check"]
    crude_claim = next(c for c in checks if "Crude exports" in c["claim"])
    assert crude_claim["validation"] == "not_reproduced_from_cited_workbook"
    assert crude_claim.get("pinned_vintage")


@pytest.mark.skipif(not CPA08.is_file(), reason="CPA08 not cached")
def test_exported_energy_matches_live_parser(energy_summary: dict) -> None:
    from src.case_studies.energy_trade import parse_cpa08_energy_trade

    trade = ONS_XLSX if ONS_XLSX.is_file() else None
    live = parse_cpa08_energy_trade(CPA08, trade_tables_path=trade)
    assert live.cpa_crude_exports.current_q_gbp_b == pytest.approx(
        energy_summary["cpa_crude_exports"]["current_q_gbp_b"], abs=0.001
    )


def test_case_studies_manifest_hashes(ni_summary: dict, energy_summary: dict) -> None:
    manifest = json.loads((SUMMARY_DIR / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["sources"]["ni_prescribing"]["sha256"] == ni_summary["sha256_source_csv"]
    assert manifest["sources"]["ons_cpa08"]["sha256"] == energy_summary["sha256_source_cpa08_xlsx"]
    assert "rebuild_label" in manifest
