"""Macro analytics static demos — data from committed pipeline JSON."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static-site"
DEMO = STATIC / "demo"


def test_manifest_matches_cpih_row_count() -> None:
    manifest = json.loads((DEMO / "manifest.json").read_text(encoding="utf-8"))
    cpih = json.loads((DEMO / "cpih_yoy.json").read_text(encoding="utf-8"))
    assert manifest["sources"]["cpih"]["rows"] == len(cpih)


def test_cpih_null_yoy_at_series_start() -> None:
    cpih = json.loads((DEMO / "cpih_yoy.json").read_text(encoding="utf-8"))
    assert cpih[0]["yoy_pct"] is None
    non_null = sum(1 for r in cpih if r.get("yoy_pct") is not None)
    assert non_null > 100


def test_macro_analytics_module_paths_in_html() -> None:
    for name in ("macro-explorer.html", "data-coverage.html"):
        html = (STATIC / "portfolio" / name).read_text(encoding="utf-8")
        assert "macro-analytics.js" in html
        js = (STATIC / "portfolio" / "assets" / "macro-analytics.js").read_text()
        assert "../../demo/manifest.json" in js


def test_ats_retired_page_has_no_submission_flow() -> None:
    ats = (STATIC / "portfolio" / "ats-matcher.html").read_text(encoding="utf-8")
    assert "retired" in ats.lower()
    assert 'src="./config.js"' not in ats
    assert "AI_BACKEND_URL" not in ats
    assert "fetch(" not in ats


@pytest.mark.parametrize(
    "rel",
    (
        "portfolio/macro-explorer.html",
        "portfolio/data-coverage.html",
    ),
)
def test_macro_demo_pages_declare_snapshot_not_live(rel: str) -> None:
    html = (STATIC / rel).read_text(encoding="utf-8")
    assert "snapshot" in html.lower() or "committed" in html.lower()
    assert 'name="color-scheme" content="dark"' in html
