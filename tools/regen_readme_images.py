#!/usr/bin/env python3
"""
Regenerate README hero and architecture images as high-DPI WebP + full-color PNG.

Targets ~2x the typical README column width so images stay sharp on Retina / mobile.

Requires Pillow: pip install pillow

  python3 tools/regen_readme_images.py

Optional masters: tools/source/hero.png (wide banner) — if missing, a vector-style
banner is drawn in code. Architecture is always drawn in code for consistent sharpness.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "tools" / "source"


def _fonts() -> tuple[ImageFont.FreeTypeFont, ImageFont.FreeTypeFont, ImageFont.FreeTypeFont]:
    try:
        bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
        regular = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except OSError:
        d = ImageFont.load_default()
        return d, d, d
    return bold, regular, small


def _save_webp(img: Image.Image, path: Path, quality: int = 90) -> None:
    img.save(path, format="WEBP", quality=quality, method=6)


def _save_png(img: Image.Image, path: Path) -> None:
    img.convert("RGB").save(path, format="PNG", optimize=True, compress_level=9)


def render_hero(width: int = 1800) -> Image.Image:
    """Wide banner with smooth gradient (full color, no heavy quantization)."""
    ar = 1200 / 400  # original aspect
    height = max(1, int(width / ar))
    img = Image.new("RGB", (width, height), color=(15, 23, 42))
    d = ImageDraw.Draw(img)
    for i in range(height):
        t = i / max(height - 1, 1)
        r = int(15 + t * 28)
        g = int(23 + t * 45)
        b = int(42 + t * 65)
        d.line([(0, i), (width, i)], fill=(r, g, b))

    # Accent header bar
    pad = int(width * 0.03)
    d.rounded_rectangle(
        [pad, pad, width - pad, int(height * 0.28)],
        radius=int(height * 0.06),
        fill=(30, 58, 138),
        outline=(59, 130, 246),
        width=max(2, width // 600),
    )

    f_title, f_sub, f_lab = _fonts()
    title = "UK Macro Analytics Engine"
    subtitle = "Open data -> Parquet cache -> DuckDB -> analytics & exports"

    tx = pad * 2
    ty = int(height * 0.11)
    d.text((tx, ty), title, fill=(248, 250, 252), font=f_title)
    d.text((tx, ty + int(height * 0.14)), subtitle, fill=(203, 213, 225), font=f_sub)

    # Pipeline pills
    bx_y = int(height * 0.52)
    bx_h = int(height * 0.2)
    labels = ["Ingest", "DuckDB", "Analytics", "Exports"]
    n = len(labels)
    inner_pad = pad
    gap = int(width * 0.012)
    bw = (width - 2 * inner_pad - gap * (n - 1)) // n
    x0 = inner_pad
    for i, lab in enumerate(labels):
        x1 = x0 + i * (bw + gap)
        d.rounded_rectangle(
            [x1, bx_y, x1 + bw, bx_y + bx_h],
            radius=int(bx_h * 0.18),
            fill=(51, 65, 85),
            outline=(148, 163, 184),
            width=1,
        )
        bbox = d.textbbox((0, 0), lab, font=f_lab)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        d.text(
            (x1 + (bw - tw) // 2, bx_y + (bx_h - th) // 2 - 2),
            lab,
            fill=(248, 250, 252),
            font=f_lab,
        )

    return img


def render_architecture(width: int = 1200) -> Image.Image:
    """Crisp pipeline diagram (flat fills, high DPI)."""
    height = int(width * 240 / 820)
    img = Image.new("RGB", (width, height), color=(15, 23, 42))
    d = ImageDraw.Draw(img)
    for i in range(height):
        t = i / max(height - 1, 1)
        r = int(15 + t * 12)
        g = int(23 + t * 20)
        b = int(42 + t * 30)
        d.line([(0, i), (width, i)], fill=(r, g, b))

    d.rounded_rectangle(
        [16, 16, width - 16, height - 16],
        radius=20,
        outline=(59, 130, 246),
        width=max(2, width // 400),
    )

    try:
        f_h = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", max(22, width // 45))
        f_b = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", max(16, width // 58))
        f_t = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", max(13, width // 72))
    except OSError:
        f_h = f_b = f_t = ImageFont.load_default()

    d.text((40, 28), "Architecture", fill=(248, 250, 252), font=f_h)
    d.text(
        (40, 28 + int(height * 0.09)),
        "High-resolution diagram — also see architecture.svg for vector",
        fill=(148, 163, 184),
        font=f_t,
    )

    # Scale boxes to width
    s = width / 820.0

    def box(
        x: float,
        y: float,
        bw: float,
        bh: float,
        title: str,
        lines: list[str],
        header_rgb: tuple[int, int, int] = (30, 58, 95),
    ) -> None:
        x1, y1, x2, y2 = x * s, y * s, (x + bw) * s, (y + bh) * s
        d.rounded_rectangle(
            [x1, y1, x2, y2],
            radius=8 * s,
            fill=header_rgb,
            outline=(59, 130, 246),
            width=max(1, int(s)),
        )
        cx = (x1 + x2) / 2
        d.text((cx, y1 + 12 * s), title, fill=(226, 232, 240), font=f_b, anchor="mm")
        ly = y1 + 32 * s
        for line in lines:
            d.text((cx, ly), line, fill=(241, 245, 249), font=f_t, anchor="mm")
            ly += 22 * s

    def arrow(x1: float, x2: float, y: float) -> None:
        ya = y * s
        x1p, x2p = x1 * s, x2 * s
        d.line([(x1p, ya), (x2p, ya)], fill=(100, 116, 139), width=max(2, int(2 * s)))
        # arrowhead
        ah = 8 * s
        d.polygon([(x2p, ya), (x2p - ah, ya - ah / 2), (x2p - ah, ya + ah / 2)], fill=(100, 116, 139))

    box(24, 70, 180, 150, "Ingestion", ["config + requests", "data_fetcher", "Parquet cache"])
    arrow(210, 256, 142)
    box(264, 70, 180, 150, "Storage", ["DuckDB", "db_engine + views", "v_cpih_core", "v_psnb_monthly"])
    arrow(450, 488, 142)
    box(500, 70, 160, 150, "Analytics", ["analytics.py", "rolling / YoY", "Parquet + JSON"])
    arrow(664, 698, 142)

    ex1, ey1, ex2, ey2 = 710 * s, 95 * s, 806 * s, 208 * s
    d.rounded_rectangle(
        [ex1, ey1, ex2, ey2],
        radius=8 * s,
        fill=(20, 83, 45),
        outline=(34, 197, 94),
        width=max(1, int(s)),
    )
    cx = (ex1 + ex2) / 2
    d.text((cx, ey1 + 28 * s), "Exports", fill=(236, 252, 203), font=f_b, anchor="mm")
    d.text((cx, ey1 + 52 * s), "data/exports/", fill=(187, 247, 208), font=f_t, anchor="mm")

    return img


def main() -> None:
    hero_path = SRC / "hero.png"
    if hero_path.is_file() and hero_path.stat().st_size > 0:
        src = Image.open(hero_path).convert("RGB")
        w0, h0 = src.size
        target_w = 1800
        if w0 < target_w:
            nh = max(1, int(h0 * target_w / w0))
            hero = src.resize((target_w, nh), Image.Resampling.LANCZOS)
        else:
            nh = max(1, int(h0 * target_w / w0))
            hero = src.resize((target_w, nh), Image.Resampling.LANCZOS)
    else:
        hero = render_hero(1800)

    arch = render_architecture(1200)

    _save_webp(hero, ROOT / "hero.webp", quality=92)
    _save_png(hero, ROOT / "hero.png")

    _save_webp(arch, ROOT / "architecture.webp", quality=92)
    _save_png(arch, ROOT / "architecture.png")

    for name in ("hero.webp", "hero.png", "architecture.webp", "architecture.png"):
        p = ROOT / name
        img = Image.open(p)
        print(f"{name}: {p.stat().st_size} bytes {img.size}")

    hw, hh = hero.size
    aw, ah = arch.size
    print()
    print("README display (CSS px) for ~2x sharpness on Retina:")
    print(f"  hero: width={hw // 2} height={hh // 2}")
    print(f"  arch: width={aw // 2} height={ah // 2}")


if __name__ == "__main__":
    main()
