"""Northern Ireland GP prescribing — Open Data NI / BSO (rebuilt in repo, AI-assisted)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import duckdb

NI_PRESCRIBING_COLUMNS: tuple[str, ...] = (
    "practice",
    "year",
    "month",
    "vtm_nm",
    "vmp_nm",
    "amp_nm",
    "presentation",
    "strength",
    "total_items",
    "total_quantity",
    "gross_cost_gbp",
    "actual_cost_gbp",
    "bnf_code",
    "bnf_chapter",
    "bnf_section",
    "bnf_paragraph",
    "bnf_sub_paragraph",
)

OPEN_DATA_NI_RESOURCE_URL = (
    "https://admin.opendatani.gov.uk/dataset/gp-prescribing-data/"
    "resource/2f8e6dd8-ef10-4442-94db-5e5f74b5c135"
)
OPEN_DATA_NI_DOWNLOAD_URL = (
    "https://admin.opendatani.gov.uk/dataset/a7b76920-bc0a-48fd-9abf-dc5ad0999886/"
    "resource/2f8e6dd8-ef10-4442-94db-5e5f74b5c135/download/05.-gp-prescribing-august-2026.csv"
)


@dataclass(frozen=True)
class PrescribingSummary:
    """One-month GP prescribing aggregates (Actual Cost / Gross Cost in GBP)."""

    period_label: str
    source_url: str
    licence: str
    detail_rows: int
    distinct_practices: int
    total_items: int
    gross_cost_gbp: float
    actual_cost_gbp: float
    bnf_chapter_04_actual_cost_gbp: float
    tirzepatide_items: int
    tirzepatide_actual_cost_gbp: float
    atorvastatin_items: int
    atorvastatin_actual_cost_gbp: float
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def ni_prescribing_sanity_checks(csv_path: Path | str) -> dict[str, Any]:
    """Independent row/cost checks used by tests (not committed JSON mirrors)."""

    path = Path(csv_path)
    con = duckdb.connect()
    names = list(NI_PRESCRIBING_COLUMNS)
    con.execute(
        f"""
        CREATE OR REPLACE TABLE gp AS
        SELECT * FROM read_csv(?, header=true, names={names}, encoding='latin-1')
        """,
        [str(path)],
    )
    checks = con.execute(
        """
        SELECT
          count(*)::BIGINT,
          count(DISTINCT practice)::BIGINT,
          min(year), max(year), min(month), max(month),
          coalesce(sum(total_items), 0)::BIGINT,
          coalesce(sum(total_quantity), 0)::DOUBLE,
          coalesce(sum(actual_cost_gbp), 0)::DOUBLE,
          coalesce(sum(gross_cost_gbp), 0)::DOUBLE,
          sum(CASE WHEN actual_cost_gbp > gross_cost_gbp + 0.01 THEN 1 ELSE 0 END)::BIGINT
        FROM gp
        """
    ).fetchone()
    con.close()
    return {
        "detail_rows": int(checks[0]),
        "distinct_practices": int(checks[1]),
        "year_min": int(checks[2]) if checks[2] is not None else None,
        "year_max": int(checks[3]) if checks[3] is not None else None,
        "month_min": int(checks[4]) if checks[4] is not None else None,
        "month_max": int(checks[5]) if checks[5] is not None else None,
        "total_items": int(checks[6]),
        "total_quantity": float(checks[7]),
        "sum_actual_cost_gbp": float(checks[8]),
        "sum_gross_cost_gbp": float(checks[9]),
        "rows_actual_gt_gross": int(checks[10]),
        "column_definitions": {
            "total_items": "Prescription items (lines), not patients",
            "total_quantity": "Dispensed quantity in presentation units",
            "actual_cost_gbp": "Actual Cost — reimbursement to contractors",
            "gross_cost_gbp": "Gross Cost — list ingredient cost",
            "bnf_chapter": "BNF chapter code for therapy-area grouping",
        },
        "drug_match_rules": {
            "tirzepatide": "presentation OR vmp_nm OR amp_nm ILIKE '%tirzepatide%'",
            "atorvastatin": "presentation OR vmp_nm OR amp_nm ILIKE '%atorvastatin%'",
            "cns_proxy": "sum(actual_cost_gbp) WHERE bnf_chapter = 4",
        },
    }


def aggregate_ni_gp_prescribing(csv_path: Path | str) -> PrescribingSummary:
    path = Path(csv_path)
    con = duckdb.connect()
    names = list(NI_PRESCRIBING_COLUMNS)
    con.execute(
        f"""
        CREATE OR REPLACE TABLE gp AS
        SELECT * FROM read_csv(?, header=true, names={names}, encoding='latin-1')
        """,
        [str(path)],
    )
    row = con.execute(
        """
        SELECT
          count(*)::BIGINT,
          count(DISTINCT practice)::BIGINT,
          coalesce(sum(total_items), 0)::BIGINT,
          coalesce(round(sum(gross_cost_gbp), 2), 0),
          coalesce(round(sum(actual_cost_gbp), 2), 0)
        FROM gp
        """
    ).fetchone()
    cns = con.execute(
        """
        SELECT coalesce(round(sum(actual_cost_gbp), 2), 0)
        FROM gp WHERE try_cast(bnf_chapter AS INTEGER) = 4
        """
    ).fetchone()[0]
    tirz = con.execute(
        """
        SELECT coalesce(sum(total_items), 0)::BIGINT, coalesce(round(sum(actual_cost_gbp), 2), 0)
        FROM gp
        WHERE lower(coalesce(presentation, '')) LIKE '%tirzepatide%'
           OR lower(coalesce(vmp_nm, '')) LIKE '%tirzepatide%'
           OR lower(coalesce(amp_nm, '')) LIKE '%tirzepatide%'
        """
    ).fetchone()
    ator = con.execute(
        """
        SELECT coalesce(sum(total_items), 0)::BIGINT, coalesce(round(sum(actual_cost_gbp), 2), 0)
        FROM gp
        WHERE lower(coalesce(presentation, '')) LIKE '%atorvastatin%'
           OR lower(coalesce(vmp_nm, '')) LIKE '%atorvastatin%'
           OR lower(coalesce(amp_nm, '')) LIKE '%atorvastatin%'
        """
    ).fetchone()
    y, m = con.execute("SELECT max(year), max(month) FROM gp").fetchone()
    period = f"{int(y)}-{int(m):02d}" if y and m else "unknown"
    con.close()
    return PrescribingSummary(
        period_label=period,
        source_url=OPEN_DATA_NI_DOWNLOAD_URL,
        licence="UK Open Government Licence (OGL)",
        detail_rows=int(row[0]),
        distinct_practices=int(row[1]),
        total_items=int(row[2]),
        gross_cost_gbp=float(row[3]),
        actual_cost_gbp=float(row[4]),
        bnf_chapter_04_actual_cost_gbp=float(cns),
        tirzepatide_items=int(tirz[0]),
        tirzepatide_actual_cost_gbp=float(tirz[1]),
        atorvastatin_items=int(ator[0]),
        atorvastatin_actual_cost_gbp=float(ator[1]),
        notes=(
            "Rebuilt Nov 2026 (AI-assisted); not proof of prior personal code.",
            "Rows are practice × presentation dispensed lines, not patients or dispensing events.",
            "Actual Cost is contractor reimbursement; Gross Cost is list — not full NHS spend.",
            "BNF chapter 4 used for 'CNS' therapy-area cost (actual cost sum).",
            "Tirzepatide matched on presentation/VMP/AMP name; atorvastatin likewise.",
        ),
    )
