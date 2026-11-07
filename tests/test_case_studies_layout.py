"""Case studies mobile overflow — optional Playwright layout gate."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tools" / "case_studies_layout_qa.mjs"


def test_case_studies_html_has_responsive_overflow_guards() -> None:
    html = (ROOT / "static-site" / "case-studies.html").read_text(encoding="utf-8")
    assert "case-studies-page" in html
    polish = (ROOT / "static-site" / "hub-visual-polish.css").read_text(encoding="utf-8")
    assert "overflow-x: clip" in polish
    assert "cs-chart-caption" in html
    assert "case-studies/app.js?v=20251107d4" in html
    assert "hub-visual-polish.css?v=20251107d4" in html


@pytest.mark.skipif(
    os.environ.get("CASE_STUDIES_LAYOUT_QA") != "1",
    reason="set CASE_STUDIES_LAYOUT_QA=1 for Playwright overflow checks",
)
def test_case_studies_layout_script_passes() -> None:
    assert SCRIPT.is_file()
    assert shutil.which("node")
    art = ROOT / ".artifacts" / "case-studies-layout-qa"
    env = os.environ.copy()
    env["CASE_STUDIES_QA_ARTIFACT_DIR"] = str(art)
    base = "http://127.0.0.1:8765"
    out = subprocess.run(
        ["node", str(SCRIPT), base],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
        env=env,
    )
    assert out.returncode == 0, out.stderr or out.stdout
    report = json.loads((art / "case-studies-layout-qa.json").read_text(encoding="utf-8"))
    assert report.get("pass") is True
