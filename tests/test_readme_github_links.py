"""
README image/link contract: relative refs must match for <img src> and <a href> per asset.

This guards against GitHub README breakages from mismatched paths/casing or accidental
absolute URLs to `main` while developing on a branch.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
# e.g. <a href="./hero.png" ...><img src="./hero.png" ...>
_LINK_IMG_PAIR = re.compile(
    r'<a\s+[^>]*href="(\.\/[^"]+\.(?:png|svg))"[^>]*>\s*<img\s+[^>]*src="(\.\/[^"]+\.(?:png|svg))"',
    re.IGNORECASE | re.DOTALL,
)


def test_readme_image_link_src_href_pairs_match() -> None:
    text = README.read_text(encoding="utf-8")
    pairs = _LINK_IMG_PAIR.findall(text)
    assert pairs, "expected at least one <a href=...><img src=...></a> image block in README"
    for href, src in pairs:
        assert href == src, (
            "README image link mismatch: "
            f"href={href!r} src={src!r} (href and src must name the same asset on GitHub)"
        )


@pytest.mark.parametrize(
    "filename",
    ("hero.png", "architecture.png", "architecture.svg"),
)
def test_readme_references_committed_files(filename: str) -> None:
    text = README.read_text(encoding="utf-8")
    needle = f"./{filename}"
    assert needle in text, f"README should reference {needle} for branch-relative rendering"
    assert (ROOT / filename).is_file(), f"missing committed file {filename}"
