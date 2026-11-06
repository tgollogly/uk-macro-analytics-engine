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
