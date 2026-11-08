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
    hub_css = (STATIC / "hub-pages.css").read_text(encoding="utf-8")
    blob = idx + hub_css
    assert "min-width: 0" in blob
    assert "minmax(min(100%" in blob
    assert "overflow-wrap: anywhere" in blob


def test_static_site_documents_readme_palette_comment() -> None:
    """Macro demo page includes the regen_readme_images palette comment marker."""
    marker = "README generator palette (tools/regen_readme_images.py)"
    assert marker in (STATIC / "demo.html").read_text(encoding="utf-8")


def test_hub_shell_stylesheets_linked_from_hub_pages() -> None:
    """Hub + demo share hub-tokens + shell-shared + hub-pages; portfolio site.css imports shell."""
    build = (STATIC / "hub-asset-build.txt").read_text(encoding="utf-8").strip()
    idx = (STATIC / "index.html").read_text(encoding="utf-8")
    demo = (STATIC / "demo.html").read_text(encoding="utf-8")
    assert f'href="./hub-tokens.css?v={build}"' in idx
    assert f'href="./shell-shared.css?v={build}"' in idx
    assert f'href="./hub-pages.css?v={build}"' in idx
    assert f'href="./shell-shared.css?v={build}"' in demo
    site_css = (STATIC / "portfolio" / "assets" / "site.css").read_text(encoding="utf-8")
    assert f"hub-tokens.css?v={build}" in site_css
    assert f"shell-shared.css?v={build}" in site_css


def test_hub_pages_avoids_duplicate_shell_import() -> None:
    """shell-shared is linked from HTML; hub-pages should not @import it again."""
    hub_pages = (STATIC / "hub-pages.css").read_text(encoding="utf-8")
    assert '@import url("./shell-shared.css")' not in hub_pages


def test_hub_cards_do_not_force_row_height_stretch() -> None:
    """Avoid min-height:100% on grid cards (causes overlap when row tracks differ)."""
    hub_pages = (STATIC / "hub-pages.css").read_text(encoding="utf-8")
    assert "min-height: 100%" not in hub_pages.split(".hub-card {", 1)[1].split("}", 1)[0]


def test_portfolio_pages_include_shared_nav_and_hub_link() -> None:
    """Hub return is via primary nav (Demos) — no duplicate nav-back row on mobile."""
    needle_nav = 'class="app-nav"'
    needle_hub = "../index.html#hub"
    for name in (
        "beneish.html",
        "heat-dome.html",
        "thermal-compare.html",
        "bundlebuilder.html",
        "macro-explorer.html",
        "data-coverage.html",
        "ats-matcher.html",
        "privacy.html",
    ):
        html = (STATIC / "portfolio" / name).read_text(encoding="utf-8")
        assert needle_nav in html, name
        assert needle_hub in html, name
        assert 'class="nav-back"' not in html, name


def test_portfolio_mirror_declares_dark_color_scheme() -> None:
    for name in (
        "beneish.html",
        "heat-dome.html",
        "thermal-compare.html",
        "ats-matcher.html",
        "bundlebuilder.html",
        "privacy.html",
    ):
        html = (STATIC / "portfolio" / name).read_text(encoding="utf-8")
        assert 'name="color-scheme" content="light"' in html, name


def test_demo_charts_use_hub_token_series_colours() -> None:
    """Demo chart lines resolve CPIH / PSNB hues from hub-tokens.css variables."""
    app = (STATIC / "demo" / "app.js").read_text(encoding="utf-8")
    assert "CPIH_LINE" in app and "--hub-chart-cpih" in app
    assert "PSNB_LINE" in app and "--hub-chart-psnb" in app
    tokens = (STATIC / "hub-tokens.css").read_text(encoding="utf-8")
    assert "--hub-chart-cpih" in tokens and "--hub-chart-psnb" in tokens


def test_portfolio_mirror_has_core_assets() -> None:
    """Portfolio hub ships CSS, macro analytics modules, and demo HTML routes."""
    p = STATIC / "portfolio"
    assert (p / "assets" / "site.css").is_file()
    assert (p / "assets" / "macro-analytics.js").is_file()
    for name in (
        "beneish.html",
        "heat-dome.html",
        "thermal-compare.html",
        "bundlebuilder.html",
        "ats-matcher.html",
        "macro-explorer.html",
        "data-coverage.html",
        "privacy.html",
    ):
        assert (p / name).is_file(), f"missing {name}"


def test_portfolio_config_points_ats_backend_at_verified_url() -> None:
    cfg = (STATIC / "portfolio" / "config.js").read_text(encoding="utf-8")
    assert (
        'AI_BACKEND_URL =\n  "https://uk-macro-ats-gate.thomasgolloglypagesdev.workers.dev/api"'
        in cfg
    )


def test_portfolio_review_ats_config_is_stub_for_independent_worker() -> None:
    """Review file kept for reference; may match shipped hub gate URL."""
    cfg = (STATIC / "portfolio" / "config.review-ats-worker.js").read_text(encoding="utf-8")
    assert "window.AI_BACKEND_URL" in cfg
    assert "uk-macro-ats-gate" in cfg
    assert "workers.dev/api" in cfg


def test_docs_describe_ats_worker_deploy_and_secrets() -> None:
    doc = (Path(__file__).resolve().parent.parent / "docs" / "ATS_API_WORKER.md").read_text(
        encoding="utf-8"
    )
    assert "uk-macro-ats-gate" in doc
    assert "uk-macro-ats-backend" in doc
    assert "GEMINI_API_KEY" in doc
    assert "ATS_INTERNAL_HMAC_SECRET" in doc
    assert "new_sqlite_classes" in doc


def test_hub_index_links_to_seven_demo_routes() -> None:
    idx = (STATIC / "index.html").read_text(encoding="utf-8")
    assert 'href="./demo.html"' in idx
    assert 'href="#hub">Demos</a>' in idx
    assert idx.lower().count('href="./portfolio/') >= 4
    assert 'href="#hub">Demos</a>' in idx
    assert 'href="./portfolio/macro-explorer.html"' in idx
    assert 'href="./portfolio/data-coverage.html"' in idx
    assert 'href="./portfolio/beneish.html"' in idx
    assert 'href="./portfolio/heat-dome.html"' in idx
    assert 'href="./portfolio/thermal-compare.html"' in idx
    assert 'href="./portfolio/bundlebuilder.html"' in idx
    assert "not</strong> claiming paid analyst" in idx.lower() or "retired" in idx.lower()


def test_mirror_privacy_describes_hub_without_active_ats() -> None:
    """Privacy page: static host, chat off, ATS retired, macro JSON demos."""
    priv = (STATIC / "portfolio" / "privacy.html").read_text(encoding="utf-8")
    assert "Static site" in priv or "static HTML" in priv
    assert "not the same deployment" not in priv.lower()
    assert "Optional chat (disabled on this mirror)" in priv
    assert "retired" in priv.lower()
    assert "macro-explorer" in priv or "Macro trend" in priv
    assert "Open-Meteo" in priv
    assert "LICENSE-portfolio.txt" in priv


def test_portfolio_footnotes_match_mirror_disclosure() -> None:
    needle = "Portfolio demos on this mirror are for demonstration only"
    for name in (
        "beneish.html",
        "heat-dome.html",
        "thermal-compare.html",
        "bundlebuilder.html",
        "macro-explorer.html",
        "data-coverage.html",
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


def test_public_hub_pages_do_not_load_ats_config_js() -> None:
    """Active hub routes must not load portfolio/config.js (no public AI POST)."""
    for rel in (
        "index.html",
        "demo.html",
        "portfolio/beneish.html",
        "portfolio/macro-explorer.html",
        "portfolio/data-coverage.html",
        "portfolio/privacy.html",
    ):
        html = (STATIC / rel).read_text(encoding="utf-8")
        assert 'src="./config.js"' not in html and 'src="config.js"' not in html, rel


def test_head_vertical_padding_preserves_wrap_horizontal_inset() -> None:
    """`.wrap` sets horizontal pad; `.head` must not reset it with `padding: … 0 …` shorthand."""
    css = (STATIC / "portfolio" / "assets" / "site.css").read_text(encoding="utf-8")
    assert "padding: 0 var(--hub-content-pad)" in css.split(".wrap {", 1)[1].split("}", 1)[0]
    head_block = css.split(".head {", 1)[1].split("}", 1)[0]
    assert "padding-block:" in head_block
    assert " 0 " not in head_block.replace("padding-block:", "")
    for marker in ("@media (max-width: 900px)", "@media (max-width: 640px)"):
        chunk = css.split(marker, 1)[1].split("@media", 1)[0]
        assert ".head" in chunk
        assert "padding-block:" in chunk
        assert "padding:" not in chunk.split(".head", 1)[1].split("}", 1)[0]


def test_compact_nav_avoids_full_width_third_row() -> None:
    """Mobile nav wraps links; title may span full row but links stay on following rows."""
    shell = (STATIC / "shell-shared.css").read_text(encoding="utf-8")
    assert "nav-back" not in shell
    assert "nav-inner" in shell and "flex-wrap" in shell
    assert "white-space: normal" in shell
    assert "overflow-wrap" in shell


def test_privacy_doc_shares_wrap_column_with_page_head() -> None:
    priv = (STATIC / "portfolio" / "privacy.html").read_text(encoding="utf-8")
    assert 'class="wrap head' in priv
    assert 'class="wrap doc"' in priv
    site = (STATIC / "portfolio" / "assets" / "site.css").read_text(encoding="utf-8")
    assert "min(760px" not in site.split(".doc", 1)[1].split("/* ---------- brand", 1)[0]


def test_portfolio_case_studies_use_wrap_cs_column() -> None:
    for name in (
        "beneish.html",
        "heat-dome.html",
        "thermal-compare.html",
        "bundlebuilder.html",
        "data-coverage.html",
    ):
        html = (STATIC / "portfolio" / name).read_text(encoding="utf-8")
        assert 'class="wrap cs"' in html, name


def test_ats_workers_wrangler_enables_observability_logs() -> None:
    """Gate + backend wrangler should enable Workers Logs for post-mortems (deploy separately)."""
    gate = (ROOT / "workers" / "ats-api" / "wrangler.toml").read_text(encoding="utf-8")
    backend = (ROOT / "workers" / "ats-api" / "wrangler.backend.toml").read_text(encoding="utf-8")
    for blob, name in ((gate, "gate"), (backend, "backend")):
        assert "[observability]" in blob, name
        assert "invocation_logs = true" in blob, name


def test_ats_upstream_timeout_documented_in_worker_core() -> None:
    """Optional worker stack retained in repo; public hub does not expose ATS UI."""
    core = (ROOT / "workers" / "ats-api" / "src" / "ats-core.ts").read_text(encoding="utf-8")
    assert "UPSTREAM_TIMEOUT_MS" in core
    assert "24_000" in core
    ats = (STATIC / "portfolio" / "ats-matcher.html").read_text(encoding="utf-8")
    assert "AbortController" not in ats
    assert "fetch(" not in ats
