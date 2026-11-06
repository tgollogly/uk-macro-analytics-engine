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

# Versioned basenames so GitHub Camo (`/.../hero-README-v2.png`) and blob/raw use one path
# (query strings like `?v=` are stripped from the raw fetch; renames bust stale CDN keys).
README_HERO_PNG = "hero-README-v2.png"
README_ARCH_PNG = "architecture-README-v2.png"
README_HERO_WEBP = "hero-README-v2.webp"
README_ARCH_WEBP = "architecture-README-v2.webp"
README_BITMAP_PNGS: tuple[str, ...] = (README_HERO_PNG, README_ARCH_PNG)

# High-contrast “poster” palette — indigo header reads very different from earlier teal banners.
BG = (254, 252, 232)  # amber-50 (warm canvas)
HEADER = (49, 46, 129)  # indigo-900
HEADER_STROKE = (67, 56, 202)  # indigo-700
ACCENT_BADGE = (251, 191, 36)  # amber-400 (step numbers)
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


def _font_bold(px: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", px)
    except OSError:
        return ImageFont.load_default()


def _font_sans(px: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", px)
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


def _longest_wrapped_line_width(
    draw: ImageDraw.ImageDraw, lines: list[str], font: ImageFont.ImageFont
) -> float:
    wmax = 0.0
    for line in lines:
        bb = draw.textbbox((0, 0), line, font=font)
        wmax = max(wmax, float(bb[2] - bb[0]))
    return wmax


def _save_webp(img: Image.Image, path: Path, quality: int = 93) -> None:
    img.save(path, format="WEBP", quality=quality, method=6)


def _save_png(img: Image.Image, path: Path) -> None:
    img.convert("RGB").save(path, format="PNG", optimize=True, compress_level=9)


def _fit_hero_header_fonts(
    width: int, text_width: int
) -> tuple[ImageFont.ImageFont, ImageFont.ImageFont, list[str], list[str]]:
    """Shrink title/body fonts until wrapped lines fit text_width (no cropping)."""
    title_str = "UK Macro Analytics Engine"
    subtitle_str = "ONS open data → Parquet → DuckDB → analytics & exports"
    scratch = ImageDraw.Draw(Image.new("RGB", (max(text_width, 100), 50), color=HEADER))
    title_px = max(76, width // 14)
    sub_px = max(36, width // 34)
    min_title = max(52, width // 24)
    min_sub = max(26, width // 52)
    while True:
        f_title = _font_bold(title_px)
        f_sub = _font_sans(sub_px)
        title_lines = _wrap_lines(scratch, title_str, f_title, text_width)
        sub_lines = _wrap_lines(scratch, subtitle_str, f_sub, text_width)
        ok = (
            _longest_wrapped_line_width(scratch, title_lines, f_title) <= text_width + 0.5
            and _longest_wrapped_line_width(scratch, sub_lines, f_sub) <= text_width + 0.5
        )
        if ok or (title_px <= min_title and sub_px <= min_sub):
            return f_title, f_sub, title_lines, sub_lines
        title_px = max(min_title, title_px - 3)
        sub_px = max(min_sub, sub_px - 2)


def render_hero(width: int = 2400) -> Image.Image:
    """Tall poster: indigo header + numbered stack; header text wrapped and font-fit to width."""
    pad = int(width * 0.055)
    inner_margin = int(width * 0.036)
    header_inner_left = pad + inner_margin
    header_inner_right = width - pad - inner_margin
    tw_header = max(120, header_inner_right - header_inner_left)

    f_title, f_sub, title_lines, sub_lines = _fit_hero_header_fonts(width, tw_header)
    lh_title = _text_line_height(f_title)
    lh_sub = _text_line_height(f_sub)
    gap_after_title = int(lh_title * 0.42)
    title_block = len(title_lines) * int(lh_title * 1.18)
    sub_block = len(sub_lines) * int(lh_sub * 1.22)
    header_content_h = title_block + gap_after_title + sub_block
    title_h = inner_margin + header_content_h + inner_margin

    f_big = _font_bold(max(60, width // 20))
    try:
        f_line = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", max(44, width // 30)
        )
    except OSError:
        f_line = ImageFont.load_default()
    f_step = _font_bold(max(96, width // 10))

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

    scratch = ImageDraw.Draw(Image.new("RGB", (width, 50), color=BG))
    lh_big = _text_line_height(f_big)
    lh_line = _text_line_height(f_line)
    row_heights: list[int] = []
    for _num, head, lines in stages:
        head_wrapped = _wrap_lines(scratch, head, f_big, tw_body)
        body_wrapped: list[str] = []
        for L in lines:
            body_wrapped.extend(_wrap_lines(scratch, L, f_line, tw_body))
        top_text = card_inset + int(lh_big * 0.15)
        head_block = len(head_wrapped) * int(lh_big * 1.2)
        gap_hb = int(lh_line * 0.25)
        body_block = len(body_wrapped) * int(lh_line * 1.28)
        bottom_margin = card_inset + int(lh_line * 1.15)
        need_inner = top_text + head_block + gap_hb + body_block + bottom_margin
        min_row = int(width * 0.14)
        rh = max(min_row, need_inner)
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
    hy = pad + inner_margin
    tx = float(header_inner_left)
    for tl in title_lines:
        d.text((tx, hy), tl, fill=(255, 255, 255), font=f_title)
        bb = d.textbbox((tx, hy), tl, font=f_title)
        assert bb[0] >= header_inner_left - 1 and bb[2] <= header_inner_right + 1, (
            f"hero title overflow: {tl!r} bbox={bb} inner=[{header_inner_left},{header_inner_right}]"
        )
        hy += int(lh_title * 1.18)
    hy += gap_after_title - int(lh_title * 0.05)
    for sl in sub_lines:
        d.text((tx, hy), sl, fill=SUBTITLE_ON_HEADER, font=f_sub)
        bb = d.textbbox((tx, hy), sl, font=f_sub)
        assert bb[0] >= header_inner_left - 1 and bb[2] <= header_inner_right + 1, (
            f"hero subtitle overflow: {sl!r} bbox={bb}"
        )
        hy += int(lh_sub * 1.22)

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

        tx_body = bx2 + int(inner_w * 0.035)
        ty = y + card_inset + int(lh_big * 0.15)
        head_wrapped = _wrap_lines(d, head, f_big, tw_body)
        ly = ty
        for hl in head_wrapped:
            d.text((tx_body, ly), hl, fill=HEADER, font=f_big)
            ly += int(lh_big * 1.2)
        ly += int(lh_line * 0.25)
        for L in lines:
            for wl in _wrap_lines(d, L, f_line, tw_body):
                d.text((tx_body, ly), wl, fill=TEXT_MUTED, font=f_line)
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
        f_banner_title = _font_bold(max(64, int(width * 0.034)))
        f_banner_sub = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", max(32, int(width * 0.02))
        )
        f_head = _font_bold(max(56, int(width * 0.031)))
        f_line = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", max(44, int(width * 0.022))
        )
        f_step = _font_bold(max(84, int(width * 0.044)))
    except OSError:
        f_banner_title = f_head = f_step = ImageFont.load_default()
        f_banner_sub = f_line = ImageFont.load_default()

    lh_head = _text_line_height(f_head)
    lh_line = _text_line_height(f_line)

    banner_top = margin + int(width * 0.02)
    banner_pad_x = int(iw * 0.04)
    tw_banner = iw - 2 * banner_pad_x
    scratch = ImageDraw.Draw(Image.new("RGB", (width, 50), color=BG))
    banner_sub_lines = _wrap_lines(
        scratch,
        "ONS open CSVs · validation · Parquet · DuckDB · analytics & exports",
        f_banner_sub,
        tw_banner,
    )
    for line in banner_sub_lines:
        assert _longest_wrapped_line_width(scratch, [line], f_banner_sub) <= tw_banner + 0.5
    banner_line_h = _text_line_height(f_banner_sub)
    banner_h = (
        int(banner_line_h * 1.5)
        + len(banner_sub_lines) * int(banner_line_h * 1.25)
        + int(width * 0.02)
    )

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
        title_lines = _wrap_lines(scratch, title, f_head, tw_text)
        body_lines: list[str] = []
        for L in lines:
            body_lines.extend(_wrap_lines(scratch, L, f_line, tw_text))
        top_pad = card_inset + int(lh_head * 0.1)
        title_block = len(title_lines) * int(lh_head * 1.22)
        gap_ht = int(lh_line * 0.4)
        body_block = len(body_lines) * int(lh_line * 1.42)
        below_last = int(lh_line * 1.65)
        inner_text = top_pad + title_block + gap_ht + body_block + below_last
        min_pill = int(width * 0.22) + 2 * card_inset
        block_heights.append(max(inner_text, min_pill))

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
    ban_title_lines = _wrap_lines(d, "Architecture", f_banner_title, tw_banner)
    sy = banner_top + int(banner_line_h * 0.72)
    for bt in ban_title_lines:
        d.text((bx, sy), bt, fill=(255, 255, 255), font=f_banner_title)
        sy += int(banner_line_h * 1.22)
    sy += int(banner_line_h * 0.35)
    for sl in banner_sub_lines:
        d.text((bx, sy), sl, fill=(199, 210, 254), font=f_banner_sub)
        bbb = d.textbbox((bx, sy), sl, font=f_banner_sub)
        inner_l2 = inner_l + banner_pad_x
        inner_r2 = inner_r - banner_pad_x
        assert bbb[0] >= inner_l2 - 1 and bbb[2] <= inner_r2 + 1, f"arch banner sub overflow {sl!r}"
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

        tx2 = bx2 + gap_after_badge
        ty = int(y) + card_inset + int(lh_head * 0.1)
        for hl in _wrap_lines(d, title, f_head, tw_text):
            d.text((tx2, ty), hl, fill=HEADER, font=f_head)
            ty += int(lh_head * 1.22)
        ty += int(lh_line * 0.4)
        for L in lines:
            for wl in _wrap_lines(d, L, f_line, tw_text):
                d.text((tx2, ty), wl, fill=TEXT_BODY, font=f_line)
                ty += int(lh_line * 1.42)

        y += blk_h
        if i < len(stages) - 1:
            down_arrow(y)
            y += arrow_h

    return img


def main() -> None:
    target_w = 2400
    hero = render_hero(target_w)
    arch = render_architecture(2400)

    _save_webp(hero, ROOT / README_HERO_WEBP, quality=94)
    _save_png(hero, ROOT / README_HERO_PNG)

    _save_webp(arch, ROOT / README_ARCH_WEBP, quality=94)
    _save_png(arch, ROOT / README_ARCH_PNG)

    source_dir = ROOT / "tools" / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    for name in README_BITMAP_PNGS:
        src = ROOT / name
        dst = source_dir / name
        dst.write_bytes(src.read_bytes())

    for name in (
        README_HERO_WEBP,
        README_HERO_PNG,
        README_ARCH_WEBP,
        README_ARCH_PNG,
    ):
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
