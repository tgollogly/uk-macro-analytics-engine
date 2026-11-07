"""Visual polish — static guards + optional Playwright motion/overflow QA."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tools" / "visual_polish_qa.mjs"


def test_polish_assets_wired() -> None:
    for name in ("hub-visual-polish.css", "hub-page-enhance.js"):
        assert (ROOT / "static-site" / name).is_file()
    story = (ROOT / "static-site" / "macro-story.html").read_text(encoding="utf-8")
    assert "data-async-root" in story
    assert "hub-visual-polish.css?v=20251107d4" in story
    assert "hub-page-enhance" in (ROOT / "static-site" / "macro-story" / "story.js").read_text(
        encoding="utf-8",
    )


@pytest.mark.skipif(
    os.environ.get("VISUAL_POLISH_QA") != "1",
    reason="set VISUAL_POLISH_QA=1 for Playwright polish checks",
)
def test_visual_polish_script_passes() -> None:
    assert SCRIPT.is_file()
    assert shutil.which("node")
    art = Path("/opt/cursor/artifacts")
    env = os.environ.copy()
    env["VISUAL_POLISH_QA_ARTIFACT_DIR"] = str(art)
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
    report = json.loads((art / "visual-polish-qa.json").read_text(encoding="utf-8"))
    assert report.get("pass") is True
