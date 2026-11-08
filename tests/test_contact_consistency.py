"""Owner contact email thomas@tgollogly.dev on hub and mirrored pages."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static-site"
OWNER = "thomas@tgollogly.dev"
MAILTO = f"mailto:{OWNER}"


def _mailtos(html: str) -> list[str]:
    return re.findall(r'href="(mailto:[^"]+)"', html)


def test_hub_index_case_studies_demo_expose_owner_email() -> None:
    for name in ("index.html", "case-studies.html", "demo.html"):
        html = (STATIC / name).read_text(encoding="utf-8")
        assert MAILTO in html, name
        assert OWNER in html, name


def test_static_site_mailto_only_owner_address() -> None:
    for path in STATIC.rglob("*.html"):
        for href in _mailtos(path.read_text(encoding="utf-8")):
            assert href == MAILTO, f"{path.relative_to(ROOT)} has {href}"


def test_evidence_handoff_lists_email_and_linkedin() -> None:
    text = (ROOT / "docs" / "EVIDENCE_HANDOFF.md").read_text(encoding="utf-8")
    assert "linkedin only" not in text.lower()
    assert OWNER in text
    assert "linkedin.com/in/thomasgollogly" in text
