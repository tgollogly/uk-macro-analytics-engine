"""Evidence handoff doc — consistent with pinned case-study JSON."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HANDOFF = ROOT / "docs" / "EVIDENCE_HANDOFF.md"
TRADE = ROOT / "static-site" / "case-studies" / "uk-energy-trade-q2-2026-summary.json"
NI = ROOT / "static-site" / "case-studies" / "ni-prescribing-2026-08-summary.json"


def test_handoff_reflects_live_site_not_review_only_stale() -> None:
    text = HANDOFF.read_text(encoding="utf-8")
    assert "production unchanged" not in text.lower()
    assert "PR #21" in text or "tgollogly.dev" in text
    assert "macro-story.html" in text and "not" in text.lower()


def test_handoff_no_public_cv_on_site() -> None:
    text = HANDOFF.read_text(encoding="utf-8")
    assert "no public cv" in text.lower() or "no public cv pdf" in text.lower()
    idx = (ROOT / "static-site" / "index.html").read_text(encoding="utf-8")
    assert "cv pdf" not in idx.lower()
    assert "thomas-gollogly-cv" not in idx.lower()


def test_handoff_energy_share_matches_json() -> None:
    text = HANDOFF.read_text(encoding="utf-8")
    trade = json.loads(TRADE.read_text(encoding="utf-8"))
    share = trade["cpa_energy_import_growth"]["share_of_goods_import_growth_pct"]
    assert abs(share - 44.2) < 0.05
    assert "44.2" in text
    assert "19.7" in text
    assert "not comparable to 44%" in text.lower() or "not comparable" in text.lower()


def test_handoff_ni_drug_rows_quantitative() -> None:
    text = HANDOFF.read_text(encoding="utf-8")
    ni = json.loads(NI.read_text(encoding="utf-8"))
    assert "9,352" in text
    assert f"{ni['atorvastatin_items']:,}" in text or str(ni["atorvastatin_items"]) in text
    assert "atorvastatin" in text.lower()
    assert "close under" not in text.lower()
    assert "bnf chapter = 4" in text.lower() or "bnf chapter = 4" in text.lower()
