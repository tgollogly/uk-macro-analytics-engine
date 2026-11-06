#!/usr/bin/env python3
"""
Regenerate README hero and architecture images as high-DPI WebP + full-color PNG.

Designed for **mobile GitHub**: flat fills, high contrast, **tall poster** layouts
(large type, stacked stages) so text stays legible at `width="100%"`.

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


def render_hero(width: int = 2400) -> Image.Image:
    """Tall poster: large title block + 2×2 stage grid (readable on narrow screens)."""
    # 3:4 portrait — lots of vertical space for type at full README width
    height = int(width * 4 / 3)
    img = Image.new("RGB", (width, height), color=BG)
    d = ImageDraw.Draw(img)

    pad = int(width * 0.055)
    title_h = int(height * 0.22)
    f_title, f_sub, f_pill, f_small = _fonts(
        max(64, width // 18),
        max(34, width // 46),
        max(40, width // 36),
        max(28, width // 52),
    )

    # Title strip — solid teal for maximum contrast
    d.rounded_rectangle(
        [pad, pad, width - pad, pad + title_h],
        radius=int(height * 0.03),
        fill=HEADER,
        outline=HEADER_STROKE,
        width=max(3, width // 400),
    )
    title = "UK Macro Analytics Engine"
    d.text((pad * 2, pad + int(title_h * 0.18)), title, fill=(255, 255, 255), font=f_title)

    sub_y = pad + int(title_h * 0.52)
    subtitle = "ONS open data → Parquet → DuckDB → analytics & exports"
    d.text((pad * 2, sub_y), subtitle, fill=SUBTITLE_ON_HEADER, font=f_sub)

    # 2×2 grid — each cell is a mini “poster” panel
    gap = int(width * 0.03)
    grid_top = pad + title_h + int(height * 0.04)
    inner_left = pad * 2
    inner_w = width - 4 * pad
    cell_w = (inner_w - gap) // 2
    cell_h = int((height - grid_top - pad * 2 - gap) / 2)

    panels: list[tuple[int, int, str, list[str]]] = [
        (0, 0, "Ingest", ["config + requests", "data_fetcher → Parquet"]),
        (1, 0, "DuckDB", ["db_engine + views", "CPIH / PSNB"]),
        (0, 1, "Analytics", ["analytics.py", "rolling · YoY"]),
        (1, 1, "Exports", ["CSV · JSON · Parquet", "data/exports/"]),
    ]

    for col, row, lab, lines in panels:
        x1 = inner_left + col * (cell_w + gap)
        y1 = grid_top + row * (cell_h + gap)
        d.rounded_rectangle(
            [x1, y1, x1 + cell_w, y1 + cell_h],
            radius=int(cell_h * 0.12),
            fill=CARD,
            outline=OUTLINE,
            width=max(2, width // 450),
        )
        cx = x1 + cell_w // 2
        ty = y1 + int(cell_h * 0.14)
        d.text((cx, ty), lab, fill=TEXT, font=f_pill, anchor="mm")
        ly = ty + int(cell_h * 0.22)
        for line in lines:
            d.text((cx, ly), line, fill=TEXT_MUTED, font=f_small, anchor="mm")
            ly += int(cell_h * 0.16)

    return img


def render_architecture(width: int = 1440) -> Image.Image:
    """Tall poster: stages stacked top-to-bottom with down arrows (matches architecture.svg)."""
    # Same aspect as SVG viewBox 720×2000
    height = int(width * 2000 / 720)
    img = Image.new("RGB", (width, height), color=BG)
    d = ImageDraw.Draw(img)

    margin = max(24, width // 25)
    d.rounded_rectangle(
        [margin, margin, width - margin, height - margin],
        radius=int(width * 0.028),
        outline=HEADER,
        width=max(4, width // 240),
        fill=(255, 255, 255),
    )

    iw = width - 2 * margin
    s = iw / 720.0

    try:
        f_h = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", max(36, int(32 * s))
        )
        f_b = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", max(28, int(26 * s))
        )
        f_t = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", max(22, int(22 * s))
        )
    except OSError:
        f_h = f_b = f_t = ImageFont.load_default()

    hx = margin + int(40 * s)
    hy = margin + int(36 * s)
    d.text((hx, hy), "Architecture", fill=TEXT, font=f_h)
    d.text(
        (hx, hy + int(48 * s)),
        "Poster layout for mobile · vector: architecture.svg",
        fill=TEXT_MUTED,
        font=f_t,
    )

    cx = width / 2
    content_top = hy + int(92 * s)
    content_bottom = height - margin - int(28 * s)

    stages: list[tuple[str, list[str], tuple[int, int, int], tuple[int, int, int], float]] = [
        ("Ingestion", ["config + requests", "data_fetcher", "Parquet cache", "ONS CSV → validated Parquet"], (240, 253, 250), HEADER, 0.21),
        ("Storage", ["DuckDB", "db_engine + views", "v_cpih_core", "v_psnb_monthly", "SQL views over Parquet"], (224, 242, 254), (3, 105, 161), 0.24),
        ("Analytics", ["analytics.py", "rolling · YoY", "Parquet + JSON", "metrics for dashboards / exports"], (255, 247, 237), (194, 65, 12), 0.21),
        ("Exports", ["data/exports/", "CSV · JSON · Parquet", "report + optional Streamlit"], (220, 252, 231), (22, 101, 52), 0.18),
    ]

    arrow_h = int((content_bottom - content_top) * 0.028)
    n_stages = len(stages)
    total_frac = sum(t[4] for t in stages)
    body_h = content_bottom - content_top - arrow_h * (n_stages - 1)
    y = content_top

    def down_arrow(y_top: float) -> None:
        ya = y_top
        yb = ya + arrow_h - 4
        d.line([(cx, ya), (cx, yb)], fill=HEADER_STROKE, width=max(5, int(5 * s)))
        ah = 14 * s
        d.polygon([(cx, ya + arrow_h), (cx - ah, yb), (cx + ah, yb)], fill=HEADER_STROKE)

    for i, (title, lines, fill, stroke, frac) in enumerate(stages):
        blk_h = int(body_h * (frac / total_frac))
        x1 = margin + int(40 * s)
        x2 = width - margin - int(40 * s)
        d.rounded_rectangle(
            [x1, y, x2, y + blk_h],
            radius=int(16 * s),
            fill=fill,
            outline=stroke,
            width=max(3, int(3 * s)),
        )
        d.text((cx, y + int(blk_h * 0.12)), title, fill=TEXT, font=f_b, anchor="mm")
        ly = y + int(blk_h * 0.28)
        line_step = max(int(blk_h * 0.11), int(22 * s))
        for line in lines:
            d.text((cx, ly), line, fill=TEXT_MUTED, font=f_t, anchor="mm")
            ly += line_step
        y += blk_h
        if i < n_stages - 1:
            down_arrow(y)
            y += arrow_h

    return img


def main() -> None:
    target_w = 2400
    # Always draw hero in code for consistent bright, high-contrast README assets.
    hero = render_hero(target_w)

    arch = render_architecture(1440)

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
