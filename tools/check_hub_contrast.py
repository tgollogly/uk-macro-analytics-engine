#!/usr/bin/env python3
"""
Approximate WCAG 2.1 contrast ratios for static-site hub token pairs.

Method: sRGB 8-bit hex -> linear RGB -> relative luminance (WCAG formula)
https://www.w3.org/TR/WCAG21/#dfn-contrast-ratio
ratio = (L1 + 0.05) / (L2 + 0.05) with L1 >= L2

Limitations: reports geometry for solid fills only; no transparency, gradients,
text strokes, or user/OS display transforms. Not a substitute for manual review
or automated tests in a real browser.

Exit 0 always; prints Markdown-friendly lines to stdout for agent/human review.
"""

from __future__ import annotations

import re
import sys


def _lin(c: float) -> float:
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def rel_luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    if len(h) != 6 or not re.fullmatch(r"[0-9a-fA-F]{6}", h):
        raise ValueError(f"expected #RRGGBB, got {hex_color!r}")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r_lin, g_lin, b_lin = _lin(r), _lin(g), _lin(b)
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def contrast_ratio(fg: str, bg: str) -> float:
    l1 = rel_luminance(fg)
    l2 = rel_luminance(bg)
    hi, lo = (l1, l2) if l1 >= l2 else (l2, l1)
    return (hi + 0.05) / (lo + 0.05)


# Pairs we care about for ordinary UI text (AA normal text >= 4.5:1; large >= 3:1)
CHECKS: tuple[tuple[str, str, str], ...] = (
    ("Hub body on ivory page", "#1a2332", "#faf8f4"),
    ("Hub muted on ivory page", "#4a5568", "#faf8f4"),
    ("Hub link on ivory page", "#1d5c8c", "#faf8f4"),
    ("Portfolio ink on white card", "#1a2332", "#ffffff"),
    ("Portfolio body on light page", "#1a2332", "#faf8f4"),
    ("Eyebrow teal on ivory", "#0d6e6e", "#faf8f4"),
    ("Cobalt section title", "#2e4a8c", "#faf8f4"),
    ("Chart legend on white card", "#1a2332", "#ffffff"),
    ("Chart tick on white card", "#4a5568", "#ffffff"),
    ("Form ink on raised field", "#1a2332", "#f7f5f1"),
    ("CPIH series title on ivory", "#9a3412", "#ffffff"),
)


def main() -> None:
    print("Hub token contrast checks (solid fills, WCAG 2.1 relative luminance)\n")
    for label, fg, bg in CHECKS:
        try:
            r = contrast_ratio(fg, bg)
        except ValueError as e:
            print(f"- **{label}**: error {e}", file=sys.stderr)
            continue
        aa_text = "≥4.5:1 AA normal" if r >= 4.5 else ("≥3:1 AA large" if r >= 3 else "below 3:1")
        print(f"- **{label}**: `{fg}` on `{bg}` → **{r:.2f}:1** ({aa_text})")


if __name__ == "__main__":
    main()
