"""Poster layout: render_hero asserts each header line fits; cover common README column widths."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from tools.regen_readme_images import render_hero

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("width", (375, 900, 2400))
def test_hero_renders_without_header_overflow(width: int) -> None:
    """render_hero asserts header line bboxes stay inside margins (see regen script)."""
    img = render_hero(width)
    assert img.width == width
    assert img.height > width


def test_committed_hero_png_matches_generator() -> None:
    path = ROOT / "hero.png"
    assert path.is_file()
    gen = render_hero(2400)
    disk = Image.open(path)
    assert disk.size == gen.size and disk.tobytes() == gen.tobytes(), (
        "hero.png out of sync — run: python3 tools/regen_readme_images.py"
    )
