#!/usr/bin/env python3
"""Generate Open Graph sharing images (1200x630) for tgollogly.dev root."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "static-site" / "og-hub-public-data-20251108a.png"
LEGACY_OUT = ROOT / "static-site" / "og-preview.png"

IVORY = (247, 245, 241)
SURFACE = (255, 255, 255)
COBALT = (46, 74, 140)
CORAL = (214, 79, 42)
TEAL = (13, 110, 110)
AMBER = (193, 127, 58)
INK = (26, 35, 50)
MUTED = (74, 85, 104)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    try:
        return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{name}", size)
    except OSError:
        return ImageFont.load_default()


def draw_card(img: Image.Image, *, headline: str, subline: str, detail: str, badge: str) -> None:
    w, h = img.size
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, w, h), fill=IVORY)
    draw.rounded_rectangle(
        (40, 36, w - 40, h - 36), radius=26, fill=SURFACE, outline=COBALT, width=3
    )
    draw.rectangle((40, 36, 46, h - 36), fill=CORAL)
    draw.rectangle((46, 36, 52, h - 36), fill=TEAL)
    draw.rectangle((52, 36, 58, h - 36), fill=AMBER)

    mark = _font(26, bold=True)
    draw.rounded_rectangle((78, 72, 146, 140), radius=16, fill=TEAL)
    draw.text((96, 94), "TG", fill=(255, 255, 255), font=mark)

    name = _font(44, bold=True)
    role = _font(30, bold=True)
    body = _font(24)
    small = _font(21)

    draw.text((168, 78), "Thomas Gollogly", fill=INK, font=name)
    draw.text((78, 162), headline, fill=COBALT, font=role)
    draw.text((78, 212), subline, fill=INK, font=body)

    y = 268
    for line in detail.split("\n"):
        draw.text((78, y), line, fill=MUTED, font=small)
        y += 34

    draw.rounded_rectangle((78, 480, 560, 548), radius=16, fill=TEAL)
    draw.text((102, 502), badge, fill=(255, 255, 255), font=small)

    draw.text((78, 562), "tgollogly.dev", fill=MUTED, font=small)


def build_hub_image() -> Image.Image:
    img = Image.new("RGB", (1200, 630), IVORY)
    draw_card(
        img,
        headline="UK public data · macro analytics",
        subline="DuckDB pipeline, ONS snapshots, traceable JSON",
        detail="Junior reporting & data technician portfolio\n"
        "CPIH · PSNB · open datasets — honest snapshot demos",
        badge="Public data · not live ONS in the browser",
    )
    return img


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Output PNG path (default: {DEFAULT_OUT.name})",
    )
    parser.add_argument(
        "--legacy-alias",
        action="store_true",
        help=f"Also write {LEGACY_OUT.name} for backwards compatibility",
    )
    args = parser.parse_args()
    img = build_hub_image()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    img.save(args.output, format="PNG", optimize=True)
    print(f"Wrote {args.output} ({args.output.stat().st_size} bytes)")
    if args.legacy_alias:
        img.save(LEGACY_OUT, format="PNG", optimize=True)
        print(f"Wrote {LEGACY_OUT} ({LEGACY_OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
