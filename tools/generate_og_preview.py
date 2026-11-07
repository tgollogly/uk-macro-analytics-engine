#!/usr/bin/env python3
"""Generate static-site/og-preview.png (1200x630) for social / LinkedIn previews."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "static-site" / "og-preview.png"

BG = (244, 246, 249)
COBALT = (46, 74, 140)
CORAL = (154, 52, 18)
TEAL = (13, 110, 110)
INK = (26, 35, 50)
MUTED = (74, 85, 104)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    try:
        return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{name}", size)
    except OSError:
        return ImageFont.load_default()


def main() -> None:
    w, h = 1200, 630
    img = Image.new("RGB", (w, h), BG)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(
        (48, 48, w - 48, h - 48),
        radius=28,
        fill=(255, 255, 255),
        outline=COBALT,
        width=3,
    )
    draw.rectangle((48, 48, 52, h - 48), fill=CORAL)
    draw.rectangle((52, 48, 56, h - 48), fill=TEAL)
    title = _font(54, bold=True)
    sub = _font(28)
    small = _font(22)
    draw.text((88, 120), "UK macro & analytics", fill=COBALT, font=title)
    draw.text((88, 195), "Evidence-led reporting demos", fill=INK, font=sub)
    draw.text(
        (88, 260),
        "ONS CPIH · PSNB pipeline · traceable JSON exports",
        fill=MUTED,
        font=small,
    )
    draw.text((88, 310), "Junior data technician portfolio — tgollogly.dev", fill=MUTED, font=small)
    draw.rounded_rectangle((88, 400, 420, 470), radius=14, fill=TEAL)
    draw.text((110, 418), "Snapshot charts, not live ONS at edge", fill=(255, 255, 255), font=small)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, format="PNG", optimize=True)
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
