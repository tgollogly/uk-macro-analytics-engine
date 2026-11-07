"""Worker cache policy and hub asset build id — warm-cache upgrade path."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static-site"
WORKER = ROOT / "workers" / "static-landing.js"
BUILD_FILE = STATIC / "hub-asset-build.txt"


def test_hub_asset_build_matches_index_and_demo() -> None:
    build = BUILD_FILE.read_text(encoding="utf-8").strip()
    assert build
    idx = (STATIC / "index.html").read_text(encoding="utf-8")
    demo = (STATIC / "demo.html").read_text(encoding="utf-8")
    assert f"hub-pages.css?v={build}" in idx
    assert f"hub-insights.js?v={build}" in idx
    assert f"hub-pages.css?v={build}" in demo
    assert f"demo/app.js?v={build}" in demo
    site_css = (STATIC / "portfolio" / "assets" / "site.css").read_text(encoding="utf-8")
    assert f"hub-tokens.css?v={build}" in site_css


def test_static_landing_sets_html_and_versioned_asset_cache() -> None:
    js = WORKER.read_text(encoding="utf-8")
    assert "must-revalidate" in js
    assert "max-age=31536000, immutable" in js
    assert "searchParams.has(\"v\")" in js
    assert "service worker" not in js.lower() or "no service worker" in js.lower()
