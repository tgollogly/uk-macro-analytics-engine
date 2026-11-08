"""Hub visual polish CSS (published pages only)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_hub_uses_visual_polish_on_index() -> None:
    assert (ROOT / "static-site" / "hub-visual-polish.css").is_file()
    html = (ROOT / "static-site" / "index.html").read_text(encoding="utf-8")
    assert "hub-visual-polish.css?v=20251108d6" in html
