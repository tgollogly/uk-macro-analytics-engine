"""Macro story bundle matches raw demo rows."""

from __future__ import annotations

import json
from pathlib import Path

from src.macro_story.compute import build_macro_story_bundle, load_demo_json

ROOT = Path(__file__).resolve().parent.parent
BUNDLE = ROOT / "static-site" / "demo" / "macro-story.json"


def test_macro_story_json_matches_compute() -> None:
    cpih, psnb, manifest = load_demo_json(ROOT)
    live = build_macro_story_bundle(cpih, psnb, manifest)
    committed = json.loads(BUNDLE.read_text(encoding="utf-8"))
    assert committed["findings"][0]["series"] == live["findings"][0]["series"]
    assert committed["cpih_yoy_last_24m"][-1]["month"] == live["cpih_yoy_last_24m"][-1]["month"]
    assert (
        committed["psnb_fy_partial_compare"]["cumulative_borrowing_gbp_m_current"]
        == live["psnb_fy_partial_compare"]["cumulative_borrowing_gbp_m_current"]
    )


def test_story_page_exists() -> None:
    html = (ROOT / "static-site" / "macro-story.html").read_text(encoding="utf-8")
    assert "macro-story.json" in html or "macro-story/story.js" in html
    assert "heatmap-host" in html


def test_findings_use_percentage_points_language() -> None:
    bundle = json.loads(BUNDLE.read_text(encoding="utf-8"))
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
