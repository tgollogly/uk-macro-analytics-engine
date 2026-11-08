"""Hub + case studies remediation guards and optional Playwright suite."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "static-site" / "index.html"


def test_hub_promotes_case_studies_and_contact() -> None:
    html = INDEX.read_text(encoding="utf-8")
    assert "macro-story.html" not in html
    assert "linkedin.com/in/thomasgollogly" in html
    assert "UK-remote junior" in html or "junior / trainee" in html
    assert "AI-assisted build" in html
    assert "CV PDF is <strong>not</strong> hosted" in html


def test_macro_story_static_not_published() -> None:
    assert not (ROOT / "static-site" / "macro-story.html").is_file()


@pytest.mark.skipif(
    os.environ.get("SITE_REMEDIATION_QA") != "1",
    reason="set SITE_REMEDIATION_QA=1 for full Playwright route QA",
)
def test_site_remediation_playwright() -> None:
    art = Path("/opt/cursor/artifacts")
    out = subprocess.run(
        ["node", str(ROOT / "tools/site_remediation_qa.mjs"), "http://127.0.0.1:8765"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=300,
        env={**os.environ, "SITE_QA_ARTIFACT_DIR": str(art)},
    )
    assert out.returncode == 0, out.stderr or out.stdout
    report = json.loads((art / "site-remediation-qa.json").read_text(encoding="utf-8"))
    assert report.get("pass") is True
