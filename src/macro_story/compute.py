"""Compute recruiter-facing macro story artifacts from pipeline snapshot JSON."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class StoryFinding:
    series: str
    headline: str
    detail: str
    period: str
    units: str
    does_not_prove: str


def _month_key(obs_date: str) -> tuple[int, int]:
    y, m, _ = obs_date.split("-")
    return int(y), int(m)


def _uk_fy(obs_date: str) -> int:
    y, m = _month_key(obs_date)
    return y if m >= 4 else y - 1


def _round_pp(x: float) -> float:
    return round(x, 2)


def _cpih_heatmap(cpih: list[dict[str, Any]], year_from: int) -> dict[str, Any]:
    cells: list[dict[str, Any]] = []
    by_cal: dict[tuple[int, int], float] = {}
    for row in cpih:
        if row.get("yoy_pct") is None:
            continue
        y, m = _month_key(row["obs_date"])
        if y < year_from:
            continue
        by_cal[(y, m)] = float(row["yoy_pct"])
        cells.append(
            {
                "year": y,
                "month": m,
                "month_label": row["obs_date"][:7],
                "yoy_pct": round(float(row["yoy_pct"]), 3),
            }
        )
    month_avgs: dict[int, float] = {}
    buckets: dict[int, list[float]] = defaultdict(list)
    for (_y, m), v in by_cal.items():
        buckets[m].append(v)
    for m, vals in buckets.items():
        month_avgs[m] = round(sum(vals) / len(vals), 3)
    return {
        "title": "CPIH year-on-year rate by calendar month",
        "year_from": year_from,
        "cells": cells,
        "calendar_month_avg_yoy_pct": {str(k): month_avgs[k] for k in sorted(month_avgs)},
        "legend": "Each cell is YoY % inflation rate (not price level falling/rising).",
    }


def _cpih_turning_points(cpih: list[dict[str, Any]], window: int = 24) -> list[dict[str, Any]]:
    valid = [r for r in cpih if r.get("yoy_pct") is not None]
    tail = valid[-window:] if len(valid) > window else valid
    out: list[dict[str, Any]] = []
    for i in range(1, len(tail) - 1):
        y0, y1, y2 = tail[i - 1]["yoy_pct"], tail[i]["yoy_pct"], tail[i + 1]["yoy_pct"]
        if y1 > y0 and y1 > y2:
            out.append(
                {
                    "kind": "local_peak",
                    "month": tail[i]["obs_date"][:7],
                    "yoy_pct": round(float(y1), 3),
                    "mom_change_pp": _round_pp(float(y1) - float(y0)),
                }
            )
        if y1 < y0 and y1 < y2:
            out.append(
                {
                    "kind": "local_trough",
                    "month": tail[i]["obs_date"][:7],
                    "yoy_pct": round(float(y1), 3),
                    "mom_change_pp": _round_pp(float(y1) - float(y0)),
                }
            )
    return out[-6:]


def _psnb_monthly_bars(psnb: list[dict[str, Any]], months: int = 24) -> list[dict[str, Any]]:
    tail = psnb[-months:]
    return [
        {
            "month": r["obs_date"][:7],
            "borrowing_gbp_m": float(r["total_net_borrowing_gbp_m"]),
            "row_count": int(r.get("row_count") or 1),
        }
        for r in tail
    ]


def _psnb_fy_compare(psnb: list[dict[str, Any]]) -> dict[str, Any]:
    by_fy: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in psnb:
        by_fy[_uk_fy(row["obs_date"])].append(row)
    latest = psnb[-1]
    fy_cur = _uk_fy(latest["obs_date"])
    fy_prior = fy_cur - 1
    cur_rows = sorted(by_fy.get(fy_cur, []), key=lambda r: r["obs_date"])
    prior_rows = sorted(by_fy.get(fy_prior, []), key=lambda r: r["obs_date"])
    if not cur_rows:
        return {"available": False}
    last_month = int(cur_rows[-1]["obs_date"][5:7])
    matched_prior = [r for r in prior_rows if int(r["obs_date"][5:7]) <= last_month]
    cur_sum = sum(float(r["total_net_borrowing_gbp_m"]) for r in cur_rows)
    prior_sum = sum(float(r["total_net_borrowing_gbp_m"]) for r in matched_prior)
    return {
        "available": True,
        "current_fy_label": f"FY {fy_cur}/{str(fy_cur + 1)[-2:]}",
        "prior_fy_label": f"FY {fy_prior}/{str(fy_prior + 1)[-2:]} (same months)",
        "months_included_current": len(cur_rows),
        "through_month": cur_rows[-1]["obs_date"][:7],
        "cumulative_borrowing_gbp_m_current": round(cur_sum, 1),
        "cumulative_borrowing_gbp_m_prior_matched": round(prior_sum, 1),
        "difference_gbp_m": round(cur_sum - prior_sum, 1),
        "note": "FY starts April; prior FY matched through same calendar month only.",
    }


def _findings(
    cpih: list[dict[str, Any]], psnb: list[dict[str, Any]], manifest: dict[str, Any]
) -> list[dict[str, Any]]:
    valid = [r for r in cpih if r.get("yoy_pct") is not None]
    latest = valid[-1]
    y, m = _month_key(latest["obs_date"])
    prior_year_row = next(
        (r for r in valid if _month_key(r["obs_date"]) == (y - 1, m)),
        None,
    )
    findings: list[StoryFinding] = []
    if prior_year_row:
        delta_pp = _round_pp(float(latest["yoy_pct"]) - float(prior_year_row["yoy_pct"]))
        findings.append(
            StoryFinding(
                series="CPIH",
                headline=f"Inflation rate {latest['obs_date'][:7]}: {latest['yoy_pct']:.2f}% YoY",
                detail=(
                    f"Same calendar month a year earlier was {prior_year_row['yoy_pct']:.2f}% YoY "
                    f"({delta_pp:+.2f} percentage points)."
                ),
                period=latest["obs_date"][:7],
                units="YoY % (rate), not price level",
                does_not_prove="Not a causal explanation; prices can rise while YoY slows.",
            )
        )
    tail24 = valid[-24:]
    peak = max(tail24, key=lambda r: r["yoy_pct"])
    trough = min(tail24, key=lambda r: r["yoy_pct"])
    findings.append(
        StoryFinding(
            series="CPIH",
            headline=f"Largest YoY in last 24m: {peak['obs_date'][:7]} ({peak['yoy_pct']:.2f}%)",
            detail=f"Smallest in window: {trough['obs_date'][:7]} ({trough['yoy_pct']:.2f}%).",
            period=f"{tail24[0]['obs_date'][:7]} – {tail24[-1]['obs_date'][:7]}",
            units="YoY %",
            does_not_prove="Local peaks are not ONS headlines unless matched to a release.",
        )
    )
    psnb_last = psnb[-1]
    psnb_bars = _psnb_monthly_bars(psnb, 24)
    hi = max(psnb_bars, key=lambda r: r["borrowing_gbp_m"])
    lo = min(psnb_bars, key=lambda r: r["borrowing_gbp_m"])
    findings.append(
        StoryFinding(
            series="PSNB",
            headline=(
                f"Latest PSNB {psnb_last['obs_date'][:7]}: "
                f"£{psnb_last['total_net_borrowing_gbp_m']:,.0f}m"
            ),
            detail=(
                f"Last 24m max {hi['month']} (£{hi['borrowing_gbp_m']:,.0f}m); "
                f"min {lo['month']} (£{lo['borrowing_gbp_m']:,.0f}m)."
            ),
            period=psnb_last["obs_date"][:7],
            units="£ million net borrowing (ex banks), monthly",
            does_not_prove="Monthly lumps reflect timing; not an annual total or policy verdict.",
        )
    )
    fy = _psnb_fy_compare(psnb)
    if fy.get("available"):
        findings.append(
            StoryFinding(
                series="PSNB",
                headline=(
                    f"{fy['current_fy_label']} borrowing through {fy['through_month']}: "
                    f"£{fy['cumulative_borrowing_gbp_m_current']:,.0f}m"
                ),
                detail=(
                    f"Matched months in {fy['prior_fy_label']}: "
                    f"£{fy['cumulative_borrowing_gbp_m_prior_matched']:,.0f}m "
                    f"(Δ £{fy['difference_gbp_m']:,.0f}m)."
                ),
                period=fy["through_month"],
                units="£ million cumulative in snapshot",
                does_not_prove="Partial FY; missing future months not zero-filled.",
            )
        )
    return [asdict(f) for f in findings]


def build_macro_story_bundle(
    cpih: list[dict[str, Any]],
    psnb: list[dict[str, Any]],
    manifest: dict[str, Any],
    *,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    now = generated_at_utc
    if not now:
        now = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    valid_years = [int(r["obs_date"][:4]) for r in cpih if r.get("yoy_pct") is not None]
    year_from = max(min(valid_years), max(valid_years) - 5) if valid_years else 2020
    return {
        "generated_at_utc": now,
        "snapshot_manifest_utc": manifest.get("generated_at_utc"),
        "sources": {
            "cpih_rows": len(cpih),
            "psnb_rows": len(psnb),
            "manifest": "static-site/demo/manifest.json",
        },
        "limitations": manifest.get("limitations", []),
        "cpih_heatmap": _cpih_heatmap(cpih, year_from),
        "cpih_turning_points_24m": _cpih_turning_points(cpih, 24),
        "cpih_yoy_last_24m": [
            {"month": r["obs_date"][:7], "yoy_pct": round(float(r["yoy_pct"]), 3)}
            for r in cpih
            if r.get("yoy_pct") is not None
        ][-24:],
        "psnb_monthly_last_24m": _psnb_monthly_bars(psnb, 24),
        "psnb_fy_partial_compare": _psnb_fy_compare(psnb),
        "findings": _findings(cpih, psnb, manifest),
    }


def load_demo_json(root: Path) -> tuple[list[dict], list[dict], dict]:
    demo = root / "static-site" / "demo"
    cpih = json.loads((demo / "cpih_yoy.json").read_text(encoding="utf-8"))
    psnb = json.loads((demo / "psnb_monthly.json").read_text(encoding="utf-8"))
    manifest = json.loads((demo / "manifest.json").read_text(encoding="utf-8"))
    return cpih, psnb, manifest


def write_macro_story_json(root: Path) -> Path:
    cpih, psnb, manifest = load_demo_json(root)
    bundle = build_macro_story_bundle(cpih, psnb, manifest)
    out = root / "static-site" / "demo" / "macro-story.json"
    out.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    return out
