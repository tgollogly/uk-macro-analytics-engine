"""Optional headless hub QA — run with HUB_BROWSER_QA=1 and Playwright installed."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tools" / "hub_browser_qa.mjs"


@pytest.mark.skipif(
    os.environ.get("HUB_BROWSER_QA") != "1",
    reason="set HUB_BROWSER_QA=1 to run Playwright smoke",
)
def test_hub_browser_qa_script_passes() -> None:
    assert SCRIPT.is_file()
    assert shutil.which("node"), "node required"
    env = os.environ.copy()
    env.setdefault(
        "HUB_QA_ARTIFACT_DIR",
        str(ROOT / ".artifacts" / "hub-browser-qa"),
    )
    out = subprocess.run(
        ["node", str(SCRIPT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=env,
        timeout=300,
    )
    assert out.returncode == 0, out.stderr or out.stdout
    report_path = Path(env["HUB_QA_ARTIFACT_DIR"]) / "hub-browser-qa-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report.get("pass") is True, report.get("errors")
