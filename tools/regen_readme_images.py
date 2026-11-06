#!/usr/bin/env python3
"""
Regenerate README hero and architecture images as high-DPI WebP + full-color PNG.

Designed for **mobile GitHub**: flat fills, high contrast, larger type (fewer
gradients = less softness when the CDN scales images).

Requires Pillow: pip install pillow

  python3 tools/regen_readme_images.py

Hero is always drawn in code for consistent, sharp README assets.
Architecture diagram is always drawn in code (matches architecture.svg theme).
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent

# Flat high-contrast palette (teal + slate) — solid fills read sharper than gradients
# when GitHub scales images on narrow viewports.
BG = (248, 250, 252)  # slate-50
HEADER = (15, 118, 110)  # teal-700
HEADER_STROKE = (13, 148, 136)  # teal-600
TEXT = (15, 23, 42)  # slate-900
TEXT_MUTED = (51, 65, 85)  # slate-700
CARD = (255, 255, 255)
OUTLINE = (13, 148, 136)  # teal-600
SUBTITLE_ON_HEADER = (204, 251, 241)  # teal-100


def _fonts(
    title: int, subtitle: int, label: int, small: int
) -> tuple[ImageFont.FreeTypeFont, ...]:
    try:
        return (
            ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", title),
            ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", subtitle),
            ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", label),
            ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", small),
        )
    except OSError:
        d = ImageFont.load_default()
        return d, d, d, d


def _save_webp(img: Image.Image, path: Path, quality: int = 93) -> None:
    img.save(path, format="WEBP", quality=quality, method=6)


def _save_png(img: Image.Image, path: Path) -> None:
    img.convert("RGB").save(path, format="PNG", optimize=True, compress_level=9)


def render_hero(width: int = 3000) -> Image.Image:
    """Bright banner, large type, high contrast pills."""
    ar = 1200 / 400
    height = max(1, int(width / ar))
    img = Image.new("RGB", (width, height), color=BG)
    d = ImageDraw.Draw(img)

    pad = int(width * 0.035)
    title_h = int(height * 0.34)
    f_title, f_sub, f_pill, _ = _fonts(
        max(56, width // 24),
        max(28, width // 54),
        max(24, width // 62),
        max(20, width // 78),
    )

    # Title strip — solid teal for maximum contrast
    d.rounded_rectangle(
        [pad, pad, width - pad, pad + title_h],
        radius=int(height * 0.07),
        fill=HEADER,
        outline=HEADER_STROKE,
        width=max(3, width // 400),
    )
    title = "UK Macro Analytics Engine"
    d.text((pad * 2, pad + int(title_h * 0.22)), title, fill=(255, 255, 255), font=f_title)

    sub_y = pad + int(title_h * 0.52)
    subtitle = "ONS open data → Parquet → DuckDB → analytics & exports"
    d.text((pad * 2, sub_y), subtitle, fill=SUBTITLE_ON_HEADER, font=f_sub)

    # Pipeline pills — white cards, dark text
    bx_y = pad + title_h + int(height * 0.06)
    bx_h = int(height * 0.26)
    labels = ["Ingest", "DuckDB", "Analytics", "Exports"]
    n = len(labels)
    gap = int(width * 0.015)
    inner = pad * 2
    bw = (width - 2 * inner - gap * (n - 1)) // n
    for i, lab in enumerate(labels):
        x1 = inner + i * (bw + gap)
        d.rounded_rectangle(
            [x1, bx_y, x1 + bw, bx_y + bx_h],
            radius=int(bx_h * 0.2),
            fill=CARD,
            outline=OUTLINE,
            width=max(2, width // 500),
        )
        bbox = d.textbbox((0, 0), lab, font=f_pill)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        d.text(
            (x1 + (bw - tw) // 2, bx_y + (bx_h - th) // 2 - 2),
            lab,
            fill=TEXT,
            font=f_pill,
        )

    return img


def render_architecture(width: int = 2400) -> Image.Image:
    """Wide architecture strip: light background, coloured stage boxes, bold text."""
    height = int(width * 280 / 1200)
    img = Image.new("RGB", (width, height), color=BG)
    d = ImageDraw.Draw(img)

    margin = max(20, width // 80)
    d.rounded_rectangle(
        [margin, margin, width - margin, height - margin],
        radius=24,
        outline=HEADER,
        width=max(3, width // 320),
        fill=(255, 255, 255),
    )

    s = (width - 2 * margin) / 1000.0

    try:
        f_h = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", max(34, int(30 * s))
        )
        f_b = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", max(26, int(22 * s))
        )
        f_t = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", max(20, int(17 * s))
        )
    except OSError:
        f_h = f_b = f_t = ImageFont.load_default()

    hx = margin + int(28 * s)
    hy = margin + int(22 * s)
    d.text((hx, hy), "Architecture", fill=TEXT, font=f_h)
    d.text(
        (hx, hy + int(36 * s)),
        "Flat high-contrast theme for README / mobile · vector: architecture.svg",
        fill=TEXT_MUTED,
        font=f_t,
    )

    # Stage colours (light fills, saturated strokes — matches architecture.svg)
    stages: list[tuple[float, float, float, float, str, list[str], tuple[int, int, int], tuple[int, int, int]]] = [
        (28, 92, 232, 168, "Ingestion", ["config + requests", "data_fetcher", "Parquet cache"], (240, 253, 250), HEADER),
        (278, 92, 232, 168, "Storage", ["DuckDB", "db_engine + views", "v_cpih_core", "v_psnb_monthly"], (224, 242, 254), (3, 105, 161)),
        (528, 92, 200, 168, "Analytics", ["analytics.py", "rolling · YoY", "Parquet + JSON"], (255, 247, 237), (194, 65, 12)),
        (748, 92, 224, 168, "Exports", ["data/exports/", "CSV · JSON · Parquet"], (220, 252, 231), (22, 101, 52)),
    ]

    y0 = margin + int(88 * s)
    for x, _y, bw, bh, title, lines, fill, stroke in stages:
        x1, y1 = margin + x * s, y0
        x2, y2 = x1 + bw * s, y1 + bh * s
        d.rounded_rectangle(
            [x1, y1, x2, y2],
            radius=14,
            fill=fill,
            outline=stroke,
            width=max(2, int(2 * s)),
        )
        cx = (x1 + x2) / 2
        d.text((cx, y1 + int(22 * s)), title, fill=TEXT, font=f_b, anchor="mm")
        ly = y1 + int(48 * s)
        for line in lines:
            d.text((cx, ly), line, fill=TEXT_MUTED, font=f_t, anchor="mm")
            ly += int(28 * s)

    # Arrows between stages
    def arrow(ax1: float, ax2: float, y: float) -> None:
        ya = y0 + y * s
        x1p, x2p = margin + ax1 * s, margin + ax2 * s
        d.line([(x1p, ya), (x2p, ya)], fill=HEADER_STROKE, width=max(3, int(3 * s)))
        ah = 12 * s
        d.polygon(
            [(x2p, ya), (x2p - ah, ya - ah * 0.45), (x2p - ah, ya + ah * 0.45)],
            fill=HEADER_STROKE,
        )

    mid_y = 72.0
    arrow(264, 276, mid_y)
    arrow(514, 526, mid_y)
    arrow(734, 746, mid_y)

    return img


def main() -> None:
    target_w = 3000
    # Always draw hero in code for consistent bright, high-contrast README assets.
    hero = render_hero(target_w)

    arch = render_architecture(2400)

    _save_webp(hero, ROOT / "hero.webp", quality=94)
    _save_png(hero, ROOT / "hero.png")

    _save_webp(arch, ROOT / "architecture.webp", quality=94)
    _save_png(arch, ROOT / "architecture.png")

    for name in ("hero.webp", "hero.png", "architecture.webp", "architecture.png"):
        p = ROOT / name
        img = Image.open(p)
        print(f"{name}: {p.stat().st_size} bytes {img.size}")

    hw, hh = hero.size
    aw, ah = arch.size
    print()
    print("Suggested README: use width=\"100%\" on <img> for full column width; files are")
    print(f"  hero {hw}x{hh}px, arch {aw}x{ah}px (~2x of typical CSS width for sharpness).")


if __name__ == "__main__":
    main()
