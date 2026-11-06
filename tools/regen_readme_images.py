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
# Slightly darker for long lines on pale card fills (mobile readability)
TEXT_BODY = (30, 41, 59)  # slate-800
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


def _text_line_height(font: ImageFont.ImageFont) -> int:
    ascent, descent = font.getmetrics()
    return ascent + descent


def _wrap_lines(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    """Word-wrap to max_width in pixels; keeps words intact where possible."""
    text = text.strip()
    if not text:
        return []
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for w in words:
        trial = " ".join(current + [w]) if current else w
        bbox = draw.textbbox((0, 0), trial, font=font)
        tw = bbox[2] - bbox[0]
        if tw <= max_width or not current:
            current.append(w)
        else:
            lines.append(" ".join(current))
            current = [w]
    if current:
        lines.append(" ".join(current))
    return lines


def _save_webp(img: Image.Image, path: Path, quality: int = 93) -> None:
    img.save(path, format="WEBP", quality=quality, method=6)


def _save_png(img: Image.Image, path: Path) -> None:
    img.convert("RGB").save(path, format="PNG", optimize=True, compress_level=9)


def render_hero(width: int = 2400) -> Image.Image:
    """Tall poster: indigo header + numbered stack; row height follows wrapped body text."""
    pad = int(width * 0.055)
    title_h = int(width * 0.26)
    f_title, f_sub, _, _ = _fonts(
        max(76, width // 15),
        max(38, width // 38),
        max(44, width // 32),
        max(30, width // 48),
    )
    f_big = _font_bold(max(56, width // 22))
    try:
        f_line = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", max(42, width // 34)
        )
        f_tag = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", max(28, width // 52)
        )
    except OSError:
        f_line = f_tag = ImageFont.load_default()
    f_step = _font_bold(max(96, width // 11))

    inner_x = pad * 2
    inner_w = width - pad * 4
    badge_w = int(inner_w * 0.11)
    gap = int(width * 0.022)
    card_inset = int(width * 0.022)
    tw_body = max(80, inner_w - badge_w - int(inner_w * 0.09))

    stages: list[tuple[str, str, list[str]]] = [
        ("1", "INGEST", ["config + requests", "data_fetcher → Parquet cache"]),
        ("2", "DUCKDB", ["db_engine + views", "CPIH · PSNB SQL views"]),
        ("3", "ANALYTICS", ["analytics.py", "rolling averages · YoY"]),
        ("4", "EXPORTS", ["data/exports/", "CSV · JSON · Parquet"]),
    ]

    # Measure row heights with wrapping (scratch draw)
    scratch = Image.new("RGB", (width, 50), color=BG)
    sd = ImageDraw.Draw(scratch)
    lh_big = _text_line_height(f_big)
    lh_line = _text_line_height(f_line)
    row_heights: list[int] = []
    for _num, head, lines in stages:
        head_wrapped = _wrap_lines(sd, head, f_big, tw_body)
        body_wrapped: list[str] = []
        for L in lines:
            body_wrapped.extend(_wrap_lines(sd, L, f_line, tw_body))
        head_h = len(head_wrapped) * int(lh_big * 1.2) + int(lh_line * 0.35)
        body_h = len(body_wrapped) * int(lh_line * 1.28)
        rh = max(int(width * 0.14), card_inset * 2 + head_h + body_h)
        row_heights.append(rh)

    stack_top = pad + title_h + int(width * 0.04)
    stack_h_total = sum(row_heights) + gap * (len(stages) - 1)
    height = stack_top + stack_h_total + pad

    img = Image.new("RGB", (width, height), color=BG)
    d = ImageDraw.Draw(img)

    d.rounded_rectangle(
        [pad, pad, width - pad, pad + title_h],
        radius=int(width * 0.018),
        fill=HEADER,
        outline=HEADER_STROKE,
        width=max(4, width // 380),
    )
    d.text((pad * 2, pad + int(title_h * 0.18)), "UK Macro Analytics Engine", fill=(255, 255, 255), font=f_title)

    sub_y = pad + int(title_h * 0.55)
    d.text(
        (pad * 2, sub_y),
        "ONS open data → Parquet → DuckDB → analytics & exports",
        fill=SUBTITLE_ON_HEADER,
        font=f_sub,
    )
    d.text(
        (pad * 2, sub_y + int(title_h * 0.28)),
        "README poster v5 · wrapped text so labels stay inside cards",
        fill=(199, 210, 254),
        font=f_tag,
    )

    y = stack_top
    for (_idx, (num, head, lines)) in enumerate(stages):
        row_h = row_heights[_idx]
        x1 = inner_x
        x2 = x1 + inner_w
        d.rounded_rectangle(
            [x1, y, x2, y + row_h],
            radius=int(min(row_h, width) * 0.06),
            fill=CARD,
            outline=OUTLINE,
            width=max(3, width // 420),
        )
        bx1 = x1 + card_inset
        bx2 = bx1 + badge_w
        by1 = y + card_inset
        by2 = y + row_h - card_inset
        d.rounded_rectangle(
            [bx1, by1, bx2, by2],
            radius=int((by2 - by1) * 0.14),
            fill=ACCENT_BADGE,
            outline=(217, 119, 6),
            width=max(2, width // 500),
        )
        d.text(((bx1 + bx2) / 2, (by1 + by2) / 2), num, fill=(67, 20, 7), font=f_step, anchor="mm")

        tx = bx2 + int(inner_w * 0.035)
        ty = y + card_inset + int(lh_big * 0.15)
        head_wrapped = _wrap_lines(d, head, f_big, tw_body)
        ly = ty
        for hl in head_wrapped:
            d.text((tx, ly), hl, fill=HEADER, font=f_big)
            ly += int(lh_big * 1.2)
        ly += int(lh_line * 0.25)
        for L in lines:
            for wl in _wrap_lines(d, L, f_line, tw_body):
                d.text((tx, ly), wl, fill=TEXT_MUTED, font=f_line)
                ly += int(lh_line * 1.28)
        y += row_h + gap

    return img


def render_architecture(width: int = 2400) -> Image.Image:
    """Tall poster: numbered stages + arrows; height grows so wrapped text fits inside cards."""
    margin = max(40, width // 22)
    inner_l = margin + int(width * 0.044)
    inner_r = width - margin - int(width * 0.044)
    iw = inner_r - inner_l

    try:
        f_banner_title = _font_bold(max(56, int(width * 0.03)))
        f_banner_sub = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", max(28, int(width * 0.017))
        )
        f_head = _font_bold(max(48, int(width * 0.028)))
        f_line = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", max(38, int(width * 0.024))
        )
        f_step = _font_bold(max(72, int(width * 0.048)))
    except OSError:
        f_banner_title = f_head = f_step = ImageFont.load_default()
        f_banner_sub = f_line = ImageFont.load_default()

    lh_head = _text_line_height(f_head)
    lh_line = _text_line_height(f_line)

    banner_top = margin + int(width * 0.02)
    banner_pad_x = int(iw * 0.04)
    tw_banner = iw - 2 * banner_pad_x
    scratch = Image.new("RGB", (width, 50), color=BG)
    sd = ImageDraw.Draw(scratch)
    banner_sub_lines = _wrap_lines(
        sd,
        "Diagram v6 · large type · vector: architecture.svg",
        f_banner_sub,
        tw_banner,
    )
    banner_line_h = _text_line_height(f_banner_sub)
    banner_h = int(banner_line_h * 1.5) + len(banner_sub_lines) * int(banner_line_h * 1.25) + int(width * 0.02)

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

    pad_x = int(iw * 0.04)
    badge_w = int(iw * 0.1)
    gap_after_badge = int(iw * 0.032)
    card_inset = int(width * 0.024)
    tw_text = max(100, iw - 2 * pad_x - badge_w - gap_after_badge)

    arrow_h = int(width * 0.028)
    block_heights: list[int] = []
    for _num, title, lines, _fill, _stroke in stages:
        title_lines = _wrap_lines(sd, title, f_head, tw_text)
        body_lines: list[str] = []
        for L in lines:
            body_lines.extend(_wrap_lines(sd, L, f_line, tw_text))
        title_h = len(title_lines) * int(lh_head * 1.22)
        body_h = len(body_lines) * int(lh_line * 1.42)
        text_stack_h = title_h + int(lh_line * 0.55) + body_h
        min_pill_h = int(width * 0.22)
        inner_h = max(text_stack_h, min_pill_h)
        block_heights.append(inner_h + 2 * card_inset)

    content_top = banner_top + banner_h + int(width * 0.028)
    height = content_top + sum(block_heights) + arrow_h * (len(stages) - 1) + margin

    img = Image.new("RGB", (width, height), color=BG)
    d = ImageDraw.Draw(img)

    outer_r = int(width * 0.028)
    d.rounded_rectangle(
        [margin, margin, width - margin, height - margin],
        radius=outer_r,
        outline=HEADER_STROKE,
        width=max(4, width // 200),
        fill=BG,
    )

    d.rounded_rectangle(
        [inner_l, banner_top, inner_r, banner_top + banner_h],
        radius=int(banner_h * 0.12),
        fill=HEADER,
        outline=HEADER_STROKE,
        width=max(2, width // 300),
    )
    bx = inner_l + banner_pad_x
    d.text((bx, banner_top + int(banner_line_h * 0.75)), "Architecture", fill=(255, 255, 255), font=f_banner_title)
    sy = banner_top + int(banner_line_h * 1.95)
    for sl in banner_sub_lines:
        d.text((bx, sy), sl, fill=(199, 210, 254), font=f_banner_sub)
        sy += int(banner_line_h * 1.22)

    cx = (inner_l + inner_r) / 2
    y = float(content_top)

    def down_arrow(y_top: float) -> None:
        ya = y_top
        yb = ya + arrow_h - 6
        d.line([(cx, ya), (cx, yb)], fill=HEADER_STROKE, width=max(5, width // 220))
        ah = width * 0.022
        d.polygon([(cx, y_top + arrow_h), (cx - ah, yb), (cx + ah, yb)], fill=HEADER_STROKE)

    for i, (num, title, lines, fill, stroke) in enumerate(stages):
        blk_h = block_heights[i]
        x1, x2 = inner_l, inner_r
        d.rounded_rectangle(
            [x1, int(y), x2, int(y) + blk_h],
            radius=int(width * 0.02),
            fill=fill,
            outline=stroke,
            width=max(3, width // 280),
        )
        bx1 = x1 + pad_x
        bx2 = bx1 + badge_w
        by1 = int(y) + card_inset
        by2 = int(y) + blk_h - card_inset
        d.rounded_rectangle(
            [bx1, by1, bx2, by2],
            radius=int((by2 - by1) * 0.12),
            fill=ACCENT_BADGE,
            outline=(180, 83, 9),
            width=max(2, width // 400),
        )
        d.text(((bx1 + bx2) / 2, (by1 + by2) / 2), num, fill=(67, 20, 7), font=f_step, anchor="mm")

        tx = bx2 + gap_after_badge
        ty = int(y) + card_inset + int(lh_head * 0.1)
        for hl in _wrap_lines(d, title, f_head, tw_text):
            d.text((tx, ty), hl, fill=HEADER, font=f_head)
            ty += int(lh_head * 1.22)
        ty += int(lh_line * 0.4)
        for L in lines:
            for wl in _wrap_lines(d, L, f_line, tw_text):
                d.text((tx, ty), wl, fill=TEXT_BODY, font=f_line)
                ty += int(lh_line * 1.42)

        y += blk_h
        if i < len(stages) - 1:
            down_arrow(y)
            y += arrow_h

    return img


def main() -> None:
    target_w = 2400
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
