#!/usr/bin/env python3
"""
Regenerate README hero and architecture images as WebP + palette PNG from high-res sources.

Requires Pillow: pip install pillow

Typical workflow: drop large PNGs as tools/source/hero.png and tools/source/architecture.png
(or adjust paths below), then:

  python3 tools/regen_readme_images.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "tools" / "source"


def _resize_rgb(img: Image.Image, max_width: int) -> Image.Image:
    img = img.convert("RGB")
    w, h = img.size
    if w <= max_width:
        return img
    scale = max_width / w
    nh = max(1, int(h * scale))
    return img.resize((max_width, nh), Image.Resampling.LANCZOS)


def _save_webp(img: Image.Image, path: Path, quality: int) -> None:
    img.save(path, format="WEBP", quality=quality, method=6)


def _save_palette_png(img: Image.Image, path: Path, colors: int) -> None:
    q = img.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    q.convert("RGB").save(path, format="PNG", optimize=True, compress_level=9)


def _save_truecolor_png(img: Image.Image, path: Path) -> None:
    """Keep gradients readable: full-color PNG (larger than palette; used as WebP fallback)."""
    img.convert("RGB").save(path, format="PNG", optimize=True, compress_level=9)


def _load_src(path: Path, fallback: Path) -> Image.Image:
    if path.is_file() and path.stat().st_size > 0:
        return Image.open(path)
    return Image.open(fallback)


def main() -> None:
    hero_src = SRC / "hero.png"
    arch_src = SRC / "architecture.png"

    h = _resize_rgb(_load_src(hero_src, ROOT / "hero.png"), 800)
    _save_webp(h, ROOT / "hero.webp", quality=78)
    _save_truecolor_png(h, ROOT / "hero.png")

    a = _resize_rgb(_load_src(arch_src, ROOT / "architecture.png"), 560)
    _save_webp(a, ROOT / "architecture.webp", quality=84)
    _save_palette_png(a, ROOT / "architecture.png", colors=64)

    for name in ("hero.webp", "hero.png", "architecture.webp", "architecture.png"):
        p = ROOT / name
        img = Image.open(p)
        print(f"{name}: {p.stat().st_size} bytes {img.size}")


if __name__ == "__main__":
    main()
