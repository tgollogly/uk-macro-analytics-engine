"""README hero/architecture assets: committed, valid PNG, synced to tools/source/."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
ASSETS = ("hero.png", "architecture.png")
MIN_WIDTH_PX = 2000


@pytest.mark.parametrize("name", ASSETS)
def test_readme_png_exists_and_valid(name: str) -> None:
    path = ROOT / name
    assert path.is_file(), f"missing {name}"
    data = path.read_bytes()
    assert data[:8] == PNG_MAGIC, f"{name} is not a PNG"
    # Poster assets: wide HiDPI canvas (regen script uses 2400px width)
    assert len(data) > 10_000, f"{name} unexpectedly small — corrupt?"
    with Image.open(path) as im:
        w, h = im.size
    assert w >= MIN_WIDTH_PX and h >= MIN_WIDTH_PX, (
        f"{name} is {w}x{h}; expected wide poster ≥{MIN_WIDTH_PX}px for README legibility"
    )


@pytest.mark.parametrize("name", ASSETS)
def test_tools_source_matches_root(name: str) -> None:
    a = ROOT / name
    b = ROOT / "tools" / "source" / name
    assert b.is_file(), f"missing tools/source/{name}"
    assert a.read_bytes() == b.read_bytes(), f"tools/source/{name} must match root {name}"
