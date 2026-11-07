"""Static guards against dark-era text tokens on the light shell."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "static-site"


def test_portfolio_ink_maps_to_hub_text_not_slate100() -> None:
    css = (SITE / "portfolio" / "assets" / "site.css").read_text(encoding="utf-8")
    assert "--ink: var(--hub-text)" in css
    assert "--ink: #e2e8f0" not in css


def test_no_dark_legend_hex_in_portfolio_html() -> None:
    macro = (SITE / "portfolio" / "macro-explorer.html").read_text(encoding="utf-8")
    assert "#e2e8f0" not in macro
    assert 'color: "#94a3b8"' not in macro


def test_chart_light_theme_module_exports() -> None:
    js = (SITE / "chart-light-theme.js").read_text(encoding="utf-8")
    assert "CHART_LEGEND" in js and "#1a2332" in js
    assert "assertLightChartTheme" in js
