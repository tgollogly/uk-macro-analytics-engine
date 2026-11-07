"""Static guards for motion CSS/JS — not a browser animation cert."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOTION_CSS = ROOT / "static-site" / "hub-motion.css"
MOTION_JS = ROOT / "static-site" / "hub-motion.js"
CHART_THEME = ROOT / "static-site" / "chart-light-theme.js"


def test_motion_css_respects_reduced_motion() -> None:
    css = MOTION_CSS.read_text(encoding="utf-8")
    assert "@view-transition" in css
    assert "prefers-reduced-motion: reduce" in css
    assert "navigation: none" in css
    assert "body.is-motion-on" in css
    assert "motion-panel-enter" in css


def test_chart_theme_exports_motion_helpers() -> None:
    js = CHART_THEME.read_text(encoding="utf-8")
    assert "chartUpdateMode" in js
    assert "chartMotionMs" in js


def test_hub_motion_exports_view_transition_helper() -> None:
    js = MOTION_JS.read_text(encoding="utf-8")
    assert "initPageMotion" in js
    assert "initViewTransitionMeta" in js
    assert "prefersReducedMotion" in js
