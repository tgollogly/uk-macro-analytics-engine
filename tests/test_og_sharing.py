"""Root Open Graph sharing metadata and immutable OG image asset."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "static-site" / "index.html"
OG = ROOT / "static-site" / "og-hub-public-data-20251108a.png"
GEN = ROOT / "tools" / "generate_og_preview.py"


def test_root_og_uses_immutable_hub_image() -> None:
    html = INDEX.read_text(encoding="utf-8")
    url = "https://tgollogly.dev/og-hub-public-data-20251108a.png"
    assert url in html
    assert 'property="og:image"' in html and "Developer" not in html
    assert 'rel="canonical" href="https://tgollogly.dev/"' in html
    assert "DuckDB" in html


def test_hub_og_image_exists_and_dimensions() -> None:
    assert OG.is_file() and OG.stat().st_size > 10_000
    try:
        from PIL import Image
    except ImportError:
        return
    with Image.open(OG) as im:
        assert im.size == (1200, 630)


def test_og_generator_script_targets_immutable_name() -> None:
    text = GEN.read_text(encoding="utf-8")
    assert "og-hub-public-data-20251108a.png" in text
