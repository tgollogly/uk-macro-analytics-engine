"""Keep docs/CASE_STUDIES.md aligned with demo manifest and JSON."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def manifest() -> dict:
    return json.loads((ROOT / "static-site" / "demo" / "manifest.json").read_text(encoding="utf-8"))


@pytest.fixture
def cpih_rows() -> list:
    return json.loads((ROOT / "static-site" / "demo" / "cpih_yoy.json").read_text(encoding="utf-8"))


@pytest.fixture
def psnb_rows() -> list:
    path = ROOT / "static-site" / "demo" / "psnb_monthly.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_case_studies_exists_and_points_to_evidence() -> None:
    md = (ROOT / "docs" / "CASE_STUDIES.md").read_text(encoding="utf-8")
    assert "## 1. UK Macro Analytics Engine" in md
    assert "pytest -q" in md
    assert "export_demo_assets.py" in md


def test_readme_contents_links_case_studies() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "[**docs/CASE_STUDIES.md**](./docs/CASE_STUDIES.md)" in readme
    assert "Case studies (junior reporting" in readme


def test_case_studies_matches_committed_demo_numbers(
    manifest: dict, cpih_rows: list, psnb_rows: list
) -> None:
    """CASE_STUDIES table must match static-site/demo (update doc after export refresh)."""
    md = (ROOT / "docs" / "CASE_STUDIES.md").read_text(encoding="utf-8")
    assert manifest["generated_at_utc"] in md
    assert str(manifest["sources"]["cpih"]["rows"]) in md
    assert str(manifest["sources"]["psnb"]["rows"]) in md

    last_yoy = None
    for r in reversed(cpih_rows):
        if r.get("yoy_pct") is not None:
            last_yoy = r
            break
    assert last_yoy is not None
    last_psnb = psnb_rows[-1]

    assert str(last_yoy["obs_date"]) in md
    assert str(last_psnb["obs_date"]) in md
    yoy = float(last_yoy["yoy_pct"])
    # Doc uses ≈ 3.672% — allow either rounded table or full precision if doc updated
    assert "3.672" in md or f"{yoy:.4f}" in md
    # PSNB may be stored as float; match integer form when whole
    borrow = last_psnb["total_net_borrowing_gbp_m"]
    assert str(int(borrow)) in md if float(borrow).is_integer() else str(borrow) in md


def test_hub_mentions_case_studies_and_manifest() -> None:
    idx = (ROOT / "static-site" / "index.html").read_text(encoding="utf-8")
    assert "CASE_STUDIES.md" in idx
    assert "docs/CASE_STUDIES.md" in idx
    assert "manifest.json" in idx


def test_demo_page_mentions_evidence_path() -> None:
    demo = (ROOT / "static-site" / "demo.html").read_text(encoding="utf-8")
    assert "manifest.json" in demo
    assert "CASE_STUDIES.md" in demo
    assert "blob/6c0bc2a06bef8960bd4291ec9e6218e1d394e8ea/docs/CASE_STUDIES.md" in demo


def test_case_studies_page_links_rebuilt_summaries() -> None:
    page = (ROOT / "static-site" / "case-studies.html").read_text(encoding="utf-8")
    assert "ni-prescribing-2026-08-summary.json" in page
    assert "uk-energy-trade-q2-2026-summary.json" in page
    assert "AI-assisted" in page


def test_case_studies_doc_lists_rebuild_totals() -> None:
    md = (ROOT / "docs" / "CASE_STUDIES.md").read_text(encoding="utf-8")
    assert "447,682" in md
    assert "CPA (08)" in md or "CPA 08" in md
    assert "src/case_studies/prescribing.py" in md
