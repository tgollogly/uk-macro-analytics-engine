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

# High-contrast “poster” palette — indigo header reads very different from earlier teal banners.
BG = (254, 252, 232)  # amber-50 (warm canvas)
HEADER = (49, 46, 129)  # indigo-900
HEADER_STROKE = (67, 56, 202)  # indigo-700
ACCENT_BADGE = (251, 191, 36)  # amber-400 (step numbers)
TEXT = (15, 23, 42)  # slate-900
TEXT_MUTED = (51, 65, 85)  # slate-700
CARD = (255, 255, 255)
OUTLINE = (79, 70, 229)  # indigo-600
SUBTITLE_ON_HEADER = (224, 231, 255)  # indigo-100


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


def _font_bold(px: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", px)
    except OSError:
        return ImageFont.load_default()


def _save_webp(img: Image.Image, path: Path, quality: int = 93) -> None:
    img.save(path, format="WEBP", quality=quality, method=6)


def _save_png(img: Image.Image, path: Path) -> None:
    img.convert("RGB").save(path, format="PNG", optimize=True, compress_level=9)


def render_hero(width: int = 2400) -> Image.Image:
    """Tall poster: indigo header + numbered vertical stack (unmistakable vs old 4-pill row)."""
    height = int(width * 5 / 3)
    img = Image.new("RGB", (width, height), color=BG)
    d = ImageDraw.Draw(img)

    pad = int(width * 0.055)
    title_h = int(height * 0.16)
    f_title, f_sub, f_big, f_line = _fonts(
        max(72, width // 16),
        max(36, width // 42),
        max(44, width // 32),
        max(30, width // 48),
    )
    f_step = _font_bold(max(110, width // 9))

    d.rounded_rectangle(
        [pad, pad, width - pad, pad + title_h],
        radius=int(height * 0.022),
        fill=HEADER,
        outline=HEADER_STROKE,
        width=max(4, width // 380),
    )
    title = "UK Macro Analytics Engine"
    d.text((pad * 2, pad + int(title_h * 0.2)), title, fill=(255, 255, 255), font=f_title)

    sub_y = pad + int(title_h * 0.58)
    subtitle = "ONS open data → Parquet → DuckDB → analytics & exports"
    d.text((pad * 2, sub_y), subtitle, fill=SUBTITLE_ON_HEADER, font=f_sub)
    d.text(
        (pad * 2, sub_y + int(title_h * 0.28)),
        "README poster v4 · vertical stack (not the old 4-box row)",
        fill=(199, 210, 254),
        font=f_line,
    )

    gap = int(height * 0.018)
    stack_top = pad + title_h + int(height * 0.035)
    stack_h = height - stack_top - pad
    n = 4
    row_h = (stack_h - gap * (n - 1)) // n
    inner_x = pad * 2
    inner_w = width - pad * 4
    badge_w = int(inner_w * 0.14)

    stages: list[tuple[str, str, list[str]]] = [
        ("1", "INGEST", ["config + requests", "data_fetcher → Parquet cache"]),
        ("2", "DUCKDB", ["db_engine + views", "CPIH · PSNB SQL views"]),
        ("3", "ANALYTICS", ["analytics.py", "rolling averages · YoY"]),
        ("4", "EXPORTS", ["data/exports/", "CSV · JSON · Parquet"]),
    ]

    y = stack_top
    for num, head, lines in stages:
        x1 = inner_x
        x2 = x1 + inner_w
        d.rounded_rectangle(
            [x1, y, x2, y + row_h],
            radius=int(row_h * 0.14),
            fill=CARD,
            outline=OUTLINE,
            width=max(3, width // 420),
        )
        bx2 = x1 + badge_w
        d.rounded_rectangle(
            [x1 + int(row_h * 0.08), y + int(row_h * 0.1), bx2, y + row_h - int(row_h * 0.1)],
            radius=int(row_h * 0.12),
            fill=ACCENT_BADGE,
            outline=(217, 119, 6),
            width=max(2, width // 500),
        )
        d.text(
            ((x1 + bx2) / 2, y + row_h // 2),
            num,
            fill=(67, 20, 7),
            font=f_step,
            anchor="mm",
        )
        tx = bx2 + int(inner_w * 0.04)
        ty = y + int(row_h * 0.18)
        d.text((tx, ty), head, fill=HEADER, font=f_big)
        ly = ty + int(row_h * 0.28)
        for line in lines:
            d.text((tx, ly), line, fill=TEXT_MUTED, font=f_line)
            ly += int(row_h * 0.2)
        y += row_h + gap

    return img


def render_architecture(width: int = 1440) -> Image.Image:
    """Tall poster: numbered stages + down arrows (matches architecture.svg)."""
    height = int(width * 2000 / 720)
    img = Image.new("RGB", (width, height), color=BG)
    d = ImageDraw.Draw(img)

    margin = max(26, width // 22)
    outer_r = int(width * 0.028)
    d.rounded_rectangle(
        [margin, margin, width - margin, height - margin],
        radius=outer_r,
        outline=HEADER_STROKE,
        width=max(4, width // 200),
        fill=BG,
    )

    inner_l = margin + int(width * 0.044)
    inner_r = width - margin - int(width * 0.044)
    iw = inner_r - inner_l

    try:
        f_banner_title = _font_bold(max(34, int(width * 0.022)))
        f_banner_sub = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", max(18, int(width * 0.012))
        )
        f_head = _font_bold(max(28, int(width * 0.019)))
        f_line = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", max(22, int(width * 0.015))
        )
        f_step = _font_bold(max(72, int(width * 0.052)))
    except OSError:
        f_banner_title = f_head = f_step = ImageFont.load_default()
        f_banner_sub = f_line = ImageFont.load_default()

    banner_h = int(height * 0.075)
    banner_top = margin + int(height * 0.02)
    d.rounded_rectangle(
        [inner_l, banner_top, inner_r, banner_top + banner_h],
        radius=int(banner_h * 0.12),
        fill=HEADER,
        outline=HEADER_STROKE,
        width=max(2, width // 300),
    )
    d.text(
        (inner_l + int(iw * 0.04), banner_top + int(banner_h * 0.32)),
        "Architecture",
        fill=(255, 255, 255),
        font=f_banner_title,
    )
    d.text(
        (inner_l + int(iw * 0.04), banner_top + int(banner_h * 0.68)),
        "Poster v4 · stacked pipeline · vector: architecture.svg",
        fill=(199, 210, 254),
        font=f_banner_sub,
    )

    content_top = banner_top + banner_h + int(height * 0.028)
    content_bottom = height - margin - int(height * 0.022)

    stages = [
        ("1", "INGESTION", ["config + requests", "data_fetcher", "Parquet cache", "ONS CSV → validated Parquet"], (240, 253, 250), HEADER),
        (
            "2",
            "STORAGE",
            ["DuckDB", "db_engine + views", "v_cpih_core", "v_psnb_monthly", "SQL views over Parquet"],
            (224, 231, 255),
            (29, 78, 216),
        ),
        (
            "3",
            "ANALYTICS",
            ["analytics.py", "rolling · YoY", "Parquet + JSON", "metrics for dashboards / exports"],
            (255, 247, 237),
            (194, 65, 12),
        ),
        ("4", "EXPORTS", ["data/exports/", "CSV · JSON · Parquet", "report + optional Streamlit"], (220, 252, 231), (22, 101, 52)),
    ]

    fracs = (0.195, 0.22, 0.195, 0.175)
    arrow_h = int((content_bottom - content_top) * 0.026)
    total_body = content_bottom - content_top - arrow_h * (len(stages) - 1)

    cx = (inner_l + inner_r) / 2
    y = float(content_top)

    def down_arrow(y_top: float) -> None:
        ya = y_top
        yb = ya + arrow_h - 6
        d.line([(cx, ya), (cx, yb)], fill=HEADER_STROKE, width=max(5, width // 220))
        ah = width * 0.022
        d.polygon([(cx, y_top + arrow_h), (cx - ah, yb), (cx + ah, yb)], fill=HEADER_STROKE)

    for i, (num, title, lines, fill, stroke) in enumerate(stages):
        blk_h = int(total_body * fracs[i])
        x1, x2 = inner_l, inner_r
        d.rounded_rectangle(
            [x1, int(y), x2, int(y) + blk_h],
            radius=int(width * 0.022),
            fill=fill,
            outline=stroke,
            width=max(3, width // 280),
        )
        pad_x = int(iw * 0.045)
        badge_w = int(iw * 0.13)
        bx1 = x1 + pad_x
        bx2 = bx1 + badge_w
        by1 = int(y) + int(blk_h * 0.12)
        by2 = int(y) + blk_h - int(blk_h * 0.12)
        d.rounded_rectangle(
            [bx1, by1, bx2, by2],
            radius=int(blk_h * 0.08),
            fill=ACCENT_BADGE,
            outline=(180, 83, 9),
            width=max(2, width // 400),
        )
        d.text(((bx1 + bx2) / 2, (by1 + by2) / 2), num, fill=(67, 20, 7), font=f_step, anchor="mm")

        tx = bx2 + int(iw * 0.035)
        ty = int(y) + int(blk_h * 0.16)
        d.text((tx, ty), title, fill=HEADER, font=f_head)
        ly = ty + int(blk_h * 0.2)
        step = int(blk_h * 0.14)
        for line in lines:
            d.text((tx, ly), line, fill=TEXT_MUTED, font=f_line)
            ly += step

        y += blk_h
        if i < len(stages) - 1:
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
