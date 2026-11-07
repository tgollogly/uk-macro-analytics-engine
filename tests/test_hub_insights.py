"""Hub insight cards — deterministic values from committed JSON."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static-site"
DEMO = STATIC / "demo"


def _load_bundle():
    manifest = json.loads((DEMO / "manifest.json").read_text(encoding="utf-8"))
    cpih = json.loads((DEMO / "cpih_yoy.json").read_text(encoding="utf-8"))
    psnb = json.loads((DEMO / "psnb_monthly.json").read_text(encoding="utf-8"))
    return manifest, cpih, psnb


def test_index_loads_hub_insights_module() -> None:
    idx = (STATIC / "index.html").read_text(encoding="utf-8")
    assert "hub-insights.js" in idx
    assert "insight-feature" in idx
    assert "takeaway-cpih" in idx
    assert "not a live ONS pull" in idx.lower() or "committed snapshot" in idx.lower()


def test_privacy_copy_is_host_neutral() -> None:
    priv = (STATIC / "portfolio" / "privacy.html").read_text(encoding="utf-8")
    assert "not the same deployment" not in priv.lower()
    assert "Static site" in priv or "static HTML" in priv.lower()


def test_compute_macro_story_matches_snapshot() -> None:
    manifest, cpih, psnb = _load_bundle()
    code = f"""
import {{
  computeMacroStory,
  latestNonNullYoY,
}} from './static-site/hub-insights.js';
const manifest = {json.dumps(manifest)};
const cpih = {json.dumps(cpih)};
const psnb = {json.dumps(psnb)};
const story = computeMacroStory(cpih, psnb, manifest);
if (story.asOfUtc !== manifest.generated_at_utc) throw new Error('asOf');
const last = latestNonNullYoY(cpih);
if (!last || story.cpih.month !== last.row.obs_date.slice(0, 7)) throw new Error('month');
if (story.cpih.yoyPct !== last.row.yoy_pct) throw new Error('yoy');
console.log('ok');
"""
    out = subprocess.run(
        ["node", "--input-type=module", "-e", code],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert out.returncode == 0, out.stderr or out.stdout
