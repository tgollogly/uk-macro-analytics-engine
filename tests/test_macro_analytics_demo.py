"""Macro analytics static demos — data from committed pipeline JSON."""

from __future__ import annotations

import json
import subprocess
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


def test_macro_explorer_documents_table_preview_cap() -> None:
    html = (STATIC / "portfolio" / "macro-explorer.html").read_text(encoding="utf-8")
    js = (STATIC / "portfolio" / "assets" / "macro-analytics.js").read_text(encoding="utf-8")
    assert 'id="view-summary"' in html
    assert "sliceTablePreview" in html
    assert "TABLE_PREVIEW_LIMIT" in js
    assert "export const TABLE_PREVIEW_LIMIT = 24" in js
    assert "capped at" in html


def test_slice_table_preview_six_and_capped_ranges() -> None:
    """Regression: 6-row range shows all 6; 120-row range caps table at 24."""
    code = """
import {
  sliceTablePreview,
  TABLE_PREVIEW_LIMIT,
} from './static-site/portfolio/assets/macro-analytics.js';
const row = (i) => ({ obs_date: `2024-${String((i % 12) + 1).padStart(2, '0')}-01` });
const six = sliceTablePreview(Array.from({ length: 6 }, (_, i) => row(i)));
if (six.capped || six.displayCount !== 6 || six.total !== 6) {
  throw new Error('expected 6 uncapped, got ' + JSON.stringify(six));
}
const many = sliceTablePreview(Array.from({ length: 120 }, (_, i) => row(i)));
if (!many.capped || many.displayCount !== TABLE_PREVIEW_LIMIT || many.total !== 120) {
  throw new Error('expected 120 capped at 24, got ' + JSON.stringify(many));
}
"""
    out = subprocess.run(
        ["node", "--input-type=module", "-e", code],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert out.returncode == 0, out.stderr or out.stdout


def test_static_site_ships_favicon_at_root() -> None:
    ico = STATIC / "favicon.ico"
    svg = STATIC / "favicon.svg"
    assert ico.is_file() and ico.stat().st_size > 32
    assert svg.is_file()
    assert ico.read_bytes()[:4] == b"\x00\x00\x01\x00"
    for rel in ("index.html", "demo.html"):
        html = (STATIC / rel).read_text(encoding="utf-8")
        assert 'href="/favicon.ico"' in html
        assert 'type="image/svg+xml"' in html


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
