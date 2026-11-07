#!/usr/bin/env python3
"""Download (if needed), aggregate, and write static-site/case-studies/*.json manifests."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "static-site" / "case-studies"
CACHE = ROOT / "data" / "cache" / "case-studies"

from src.case_studies.energy_trade import (  # noqa: E402, I001
    DEFAULT_CPA08_XLSX_URL,
    DEFAULT_TRADE_XLSX_URL,
    parse_cpa08_energy_trade,
)
from src.case_studies.prescribing import (  # noqa: E402
    OPEN_DATA_NI_DOWNLOAD_URL as NI_URL,
    aggregate_ni_gp_prescribing,
    ni_prescribing_sanity_checks,
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size > 0:
        return
    r = requests.get(url, headers={"User-Agent": "uk-macro-analytics-engine/0.1"}, timeout=300)
    r.raise_for_status()
    dest.write_bytes(r.content)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    ni_csv = CACHE / "ni-gp-prescribing-2026-08.csv"
    ons_xlsx = CACHE / "tradepublicationtables2026aug.xlsx"
    cpa_xlsx = CACHE / "cpapublicationq22026august.xlsx"
    download(NI_URL, ni_csv)
    download(DEFAULT_TRADE_XLSX_URL, ons_xlsx)
    download(DEFAULT_CPA08_XLSX_URL, cpa_xlsx)

    pres = aggregate_ni_gp_prescribing(ni_csv)
    sanity = ni_prescribing_sanity_checks(ni_csv)
    energy = parse_cpa08_energy_trade(cpa_xlsx, trade_tables_path=ons_xlsx)
    now = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    manifest = {
        "generated_at_utc": now,
        "rebuild_label": "AI-assisted recreation in uk-macro-analytics-engine (Nov 2026)",
        "sources": {
            "ni_prescribing": {
                "title": "GP Prescribing Northern Ireland - August 2026",
                "resource_page": "https://admin.opendatani.gov.uk/dataset/gp-prescribing-data/resource/2f8e6dd8-ef10-4442-94db-5e5f74b5c135",
                "download_url": NI_URL,
                "licence": "UK Open Government Licence (OGL)",
                "sha256": sha256_file(ni_csv),
                "local_cache": str(ni_csv.relative_to(ROOT)),
            },
            "ons_trade_tables_sitc_substitute": {
                "title": "UK trade publication tables (Aug 2026 vintage)",
                "dataset_page": energy.source_trade_tables_page,
                "download_url": DEFAULT_TRADE_XLSX_URL,
                "bulletin_url": energy.bulletin_url,
                "sha256": sha256_file(ons_xlsx),
                "local_cache": str(ons_xlsx.relative_to(ROOT)),
            },
            "ons_cpa08": {
                "title": "Trade in goods: CPA (08) exports and imports",
                "dataset_page": energy.source_cpa_page,
                "download_url": DEFAULT_CPA08_XLSX_URL,
                "sha256": sha256_file(cpa_xlsx),
                "local_cache": str(cpa_xlsx.relative_to(ROOT)),
            },
        },
    }
    pres_out = {
        **pres.to_dict(),
        "generated_at_utc": now,
        "sha256_source_csv": manifest["sources"]["ni_prescribing"]["sha256"],
        "sanity_checks": sanity,
        "linkedin_screenshot_comparison": {
            "status": "independent_recompute",
            "note": (
                "Aug 2026 OpenDataNI aggregates below closely match reported screenshot totals; "
                "Not proof of prior authorship — public CSV supports similar magnitudes."
            ),
        },
    }
    energy_out = {
        **energy.to_dict(),
        "generated_at_utc": now,
        "sha256_source_cpa08_xlsx": manifest["sources"]["ons_cpa08"]["sha256"],
        "sha256_source_trade_tables_xlsx": manifest["sources"][
            "ons_trade_tables_sitc_substitute"
        ]["sha256"],
    }

    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    ni_path = OUT / "ni-prescribing-2026-08-summary.json"
    ni_path.write_text(json.dumps(pres_out, indent=2), encoding="utf-8")
    trade_path = OUT / "uk-energy-trade-q2-2026-summary.json"
    trade_path.write_text(json.dumps(energy_out, indent=2), encoding="utf-8")
    print(json.dumps({"out": str(OUT), "prescribing_items": pres.total_items}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
