"""Static-site pages include software copyright, MIT, OGL, and no-warranty text (README-aligned)."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static-site"

NEEDLE_GROUPS = (
    # Software / author (LICENSE + README Legal section)
    ("Thomas Gollogly", "MIT License"),
    # Third-party statistics (README + NOTICE)
    ("Crown copyright", "Open Government Licence"),
    # Disclaimer (README Legal — same clauses; HTML may split with <strong>)
    ("without warranty", "official ONS releases"),
    ("NOTICE.md",),
)


@pytest.mark.parametrize("rel", ("index.html", "demo.html"))
def test_static_pages_include_attribution_and_legal(rel: str) -> None:
    text = (STATIC / rel).read_text(encoding="utf-8")
    for group in NEEDLE_GROUPS:
        for needle in group:
            assert needle in text, f"{rel} must mention {needle!r}"


def test_hub_index_narrow_layout_constraints() -> None:
    """Cards and wraps avoid flex/grid min-content blowout (overflow) on narrow viewports."""
    idx = (STATIC / "index.html").read_text(encoding="utf-8")
    assert "min-width: 0" in idx
    assert "minmax(min(100%" in idx
    assert "overflow-wrap: anywhere" in idx


def test_static_site_documents_readme_palette_comment() -> None:
    """Both HTML pages include the regen_readme_images palette comment marker."""
    marker = "README generator palette (tools/regen_readme_images.py)"
    assert marker in (STATIC / "index.html").read_text(encoding="utf-8")
    assert marker in (STATIC / "demo.html").read_text(encoding="utf-8")


def test_demo_charts_use_architecture_stage_stroke_hex() -> None:
    """Demo chart lines use ANALYTICS / EXPORTS stage stroke hex from regen_readme_images."""
    app = (STATIC / "demo" / "app.js").read_text(encoding="utf-8")
    assert "CPIH_LINE" in app and "#c2410c" in app  # ANALYTICS stroke (194, 65, 12)
    assert "PSNB_LINE" in app and "#166534" in app  # EXPORTS stroke (22, 101, 52)


def test_portfolio_mirror_has_core_assets() -> None:
    """Mirrored portfolio demos ship CSS + config + five demo HTML files."""
    p = STATIC / "portfolio"
    assert (p / "assets" / "site.css").is_file()
    assert (p / "config.js").is_file()
    for name in (
        "beneish.html",
        "heat-dome.html",
        "thermal-compare.html",
        "bundlebuilder.html",
        "ats-matcher.html",
        "privacy.html",
    ):
        assert (p / name).is_file(), f"missing mirrored {name}"


def test_portfolio_config_points_ats_backend_at_verified_url() -> None:
    cfg = (STATIC / "portfolio" / "config.js").read_text(encoding="utf-8")
    assert 'AI_BACKEND_URL = "https://tgollogly.dev/api"' in cfg


def test_hub_index_links_to_six_demo_routes() -> None:
    idx = (STATIC / "index.html").read_text(encoding="utf-8")
    assert 'href="./demo.html"' in idx
    assert 'href="./portfolio/beneish.html"' in idx
    assert 'href="./portfolio/heat-dome.html"' in idx
    assert 'href="./portfolio/thermal-compare.html"' in idx
    assert 'href="./portfolio/ats-matcher.html"' in idx
    assert 'href="./portfolio/bundlebuilder.html"' in idx


def test_mirror_privacy_discloses_static_host_and_ats_backend() -> None:
    """Mirrored privacy page describes hub host, chat off, ATS POST, no audited no-cookie claim."""
    priv = (STATIC / "portfolio" / "privacy.html").read_text(encoding="utf-8")
    assert "Static mirror" in priv
    assert "Optional chat (disabled on this mirror)" in priv
    assert "https://tgollogly.dev/api" in priv
    assert "Open-Meteo" in priv
    assert "LICENSE-portfolio.txt" in priv


def test_portfolio_footnotes_match_mirror_disclosure() -> None:
    needle = "Portfolio demos on this mirror are for demonstration only"
    for name in (
        "beneish.html",
        "heat-dome.html",
        "thermal-compare.html",
        "bundlebuilder.html",
        "ats-matcher.html",
        "privacy.html",
    ):
        assert needle in (STATIC / "portfolio" / name).read_text(encoding="utf-8"), name


def test_heat_dome_uses_osm_tiles_not_carto() -> None:
    """CARTO basemap now requires a key; mirror uses OSM raster tiles (no key)."""
    hd = (STATIC / "portfolio" / "heat-dome.html").read_text(encoding="utf-8")
    assert "basemaps.cartocdn.com" not in hd
    assert "tile.openstreetmap.org" in hd


def test_heat_dome_stacks_map_above_charts_on_narrow() -> None:
    """On small viewports, map column is ordered above the readout/sparkline."""
    hd = (STATIC / "portfolio" / "heat-dome.html").read_text(encoding="utf-8")
    assert '.layout .col-map{order:1;}' in hd
    assert '.layout .col-left{order:2;}' in hd


def test_ats_matcher_parses_non_json_backend_errors() -> None:
    """ATS must not treat HTML error pages as JSON with d.error from API."""
    ats = (STATIC / "portfolio" / "ats-matcher.html").read_text(encoding="utf-8")
    assert "readAiResponse" in ats
    assert "formatAiHttpError" in ats
    assert ".json()" not in ats


def test_sitebar_narrow_wrap_prevents_back_link_clip() -> None:
    """Portfolio site.css: back link can wrap on narrow viewports (avoid clipped 'All demos')."""
    css = (STATIC / "portfolio" / "assets" / "site.css").read_text(encoding="utf-8")
    assert ".sitebar .back{flex:1 1 100%" in css or "flex: 1 1 100%" in css
    assert ".sitebar .in{" in css and "flex-wrap:wrap" in css


def test_ats_remote_error_adds_verify_hint_for_server_diagnostics() -> None:
    """When API returns JSON {error: '...GEMINI...'}, UI must label as remote message."""
    ats = (STATIC / "portfolio" / "ats-matcher.html").read_text(encoding="utf-8")
    assert "function formatRemoteApiError" in ats
    assert "Remote API message" in ats
    assert "formatRemoteApiError(d.error)" in ats
