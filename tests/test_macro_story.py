"""Macro story compute (library); static story page not published on landing."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.macro_story.compute import build_macro_story_bundle, load_demo_json

ROOT = Path(__file__).resolve().parent.parent
BUNDLE = ROOT / "static-site" / "demo" / "macro-story.json"
STORY_HTML = ROOT / "static-site" / "macro-story.html"


def test_macro_story_bundle_matches_snapshot_rows() -> None:
    cpih, psnb, manifest = load_demo_json(ROOT)
    live = build_macro_story_bundle(cpih, psnb, manifest)
    assert live["findings"][0]["series"]
    assert live["cpih_yoy_last_24m"][-1]["month"]
    if BUNDLE.is_file():
        committed = json.loads(BUNDLE.read_text(encoding="utf-8"))
        assert committed["cpih_yoy_last_24m"][-1]["month"] == live["cpih_yoy_last_24m"][-1]["month"]


@pytest.mark.skipif(
    not STORY_HTML.is_file(),
    reason="macro story HTML not published on static landing",
)
def test_story_page_exists_when_published() -> None:
    html = STORY_HTML.read_text(encoding="utf-8")
    assert "macro-story.json" in html or "macro-story/story.js" in html
    assert "heatmap-host" in html


def test_findings_use_percentage_points_language() -> None:
    cpih, psnb, manifest = load_demo_json(ROOT)
    bundle = build_macro_story_bundle(cpih, psnb, manifest)
    cpih_line = next(
        f for f in bundle["findings"]
        if f["series"] == "CPIH" and "percentage points" in f["detail"]
    )
    assert cpih_line
    assert "rate" in bundle["cpih_heatmap"]["legend"].lower()


def test_heatmap_cells_align_with_cpih() -> None:
    cpih, psnb, manifest = load_demo_json(ROOT)
    bundle = build_macro_story_bundle(cpih, psnb, manifest)
    sample = bundle["cpih_heatmap"]["cells"][-1]
    row = next(r for r in cpih if r["obs_date"].startswith(sample["month_label"]))
    assert round(float(row["yoy_pct"]), 3) == sample["yoy_pct"]
