"""Case studies chart captions and mobile overflow — optional Playwright QA."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tools" / "case_studies_layout_qa.mjs"
APP = ROOT / "static-site" / "case-studies" / "app.js"


def test_case_studies_html_has_dom_captions_and_overflow_guards() -> None:
    html = (ROOT / "static-site" / "case-studies.html").read_text(encoding="utf-8")
    assert "case-studies-page" in html
    assert "overflow-x: clip" in html
    assert "ni-chart-caption" in html
    assert "trade-chart-caption" in html
    assert "case-studies/app.js?v=20251108d6" in html


def test_case_studies_js_has_no_canvas_kpi_plugins() -> None:
    js = APP.read_text(encoding="utf-8")
    assert "afterDraw" not in js
    assert "ni-chart-caption" in js
    assert "trade-chart-caption" in js


def test_hub_asset_build_bumped() -> None:
    build = (ROOT / "static-site" / "hub-asset-build.txt").read_text(encoding="utf-8").strip()
    assert build == "20251108d6"


@pytest.mark.skipif(
    os.environ.get("CASE_STUDIES_LAYOUT_QA") != "1",
    reason="set CASE_STUDIES_LAYOUT_QA=1 for Playwright caption/layout checks",
)
def test_case_studies_layout_script_passes() -> None:
    assert SCRIPT.is_file()
    assert shutil.which("node")
    art = Path("/opt/cursor/artifacts")
    env = os.environ.copy()
    env["CASE_STUDIES_QA_ARTIFACT_DIR"] = str(art)
    base = "http://127.0.0.1:8765"
    out = subprocess.run(
        ["node", str(SCRIPT), base],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
        env=env,
    )
    assert out.returncode == 0, out.stderr or out.stdout
    report = json.loads((art / "case-studies-caption-qa.json").read_text(encoding="utf-8"))
    assert report.get("pass") is True
