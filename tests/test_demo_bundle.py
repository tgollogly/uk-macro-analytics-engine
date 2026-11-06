"""Committed static-site demo bundle: valid JSON, manifest + row count sanity."""

from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / "static-site" / "demo"


def test_demo_json_parse_and_finite() -> None:
    cpih = json.loads((DEMO / "cpih_yoy.json").read_text(encoding="utf-8"))
    psnb = json.loads((DEMO / "psnb_monthly.json").read_text(encoding="utf-8"))
    man = json.loads((DEMO / "manifest.json").read_text(encoding="utf-8"))
    assert isinstance(cpih, list) and isinstance(psnb, list)
    assert man["sources"]["cpih"]["rows"] == len(cpih)
    assert man["sources"]["psnb"]["rows"] == len(psnb)
    for row in cpih[:50]:
        for k in ("yoy_pct", "index_level", "cpih_3m_avg", "index_12m_ago"):
            v = row.get(k)
            if v is None:
                continue
            assert isinstance(v, int | float)
            assert math.isfinite(float(v))


