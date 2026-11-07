"""UK trade — CPA (08) energy lines + optional SITC 3 substitute from publication tables."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import openpyxl

ONS_PUBLICATION_TABLES_PAGE = (
    "https://www.ons.gov.uk/economy/nationalaccounts/balanceofpayments/"
    "datasets/uktradegoodsandservicespublicationtables/current"
)
ONS_CPA08_PAGE = (
    "https://www.ons.gov.uk/economy/nationalaccounts/balanceofpayments/"
    "datasets/publicationtablesuktradecpa08/current"
)
ONS_TRADE_BULLETIN_JUNE_2026 = (
    "https://www.ons.gov.uk/economy/nationalaccounts/balanceofpayments/bulletins/uktrade/june2026"
)
DEFAULT_TRADE_XLSX_URL = (
    "https://www.ons.gov.uk/file?uri=/economy/nationalaccounts/balanceofpayments/"
    "datasets/uktradegoodsandservicespublicationtables/current/"
    "tradepublicationtables2026aug.xlsx"
)
DEFAULT_CPA08_XLSX_URL = (
    "https://www.ons.gov.uk/file?uri=/economy/nationalaccounts/balanceofpayments/"
    "datasets/publicationtablesuktradecpa08/current/cpapublicationq22026august.xlsx"
)
# Back-compat alias used by export script
DEFAULT_XLSX_URL = DEFAULT_TRADE_XLSX_URL

SHEET_QUARTERLY_CP = "2 - Quarterly CP"
SHEET_CPA_EXPORTS_Q = "2. Exports quarter"
SHEET_CPA_IMPORTS_Q = "4. Imports quarter"
COMPARE_QUARTER_PRIOR = "2025 Q2"
COMPARE_QUARTER_CURRENT = "2026 Q2"

CPA_CRUDE_EXPORT = "06.1 Crude petroleum"
CPA_CRUDE_GAS_IMPORT = "06 Crude petroleum & natural gas"
CPA_REFINED_IMPORT = "19.2 Refined petroleum products"
CPA_TOTAL_EXPORTS = "Total exports"
CPA_TOTAL_IMPORTS = "Total imports"


@dataclass(frozen=True)
class CpaQuarterLevel:
    """One CPA product line: values in £ billion (from £ million table)."""

    cpa_label: str
    direction: str
    series_id: str
    prior_q_gbp_b: float
    current_q_gbp_b: float

    @property
    def yoy_change_gbp_b(self) -> float:
        return round(self.current_q_gbp_b - self.prior_q_gbp_b, 3)

    @property
    def yoy_change_pct(self) -> float | None:
        if not self.prior_q_gbp_b:
            return None
        return round(
            (self.current_q_gbp_b - self.prior_q_gbp_b) / self.prior_q_gbp_b * 100,
            1,
        )


def _cpa_row_dict(row: CpaQuarterLevel) -> dict[str, Any]:
    d = asdict(row)
    d["yoy_change_gbp_b"] = row.yoy_change_gbp_b
    d["yoy_change_pct"] = row.yoy_change_pct
    return d


@dataclass(frozen=True)
class FuelQuarterRow:
    """SITC-based substitute (Table 2A), not CPA product taxonomy."""

    direction: str
    commodity: str
    area: str
    series_id: str
    q1_2026_gbp_m: float
    q2_2026_gbp_m: float

    @property
    def qoq_change_gbp_m(self) -> float:
        return round(self.q2_2026_gbp_m - self.q1_2026_gbp_m, 1)

    @property
    def qoq_change_pct(self) -> float | None:
        if not self.q1_2026_gbp_m:
            return None
        return round((self.q2_2026_gbp_m - self.q1_2026_gbp_m) / self.q1_2026_gbp_m * 100, 1)


def _fuel_row_dict(row: FuelQuarterRow) -> dict[str, Any]:
    d = asdict(row)
    d["qoq_change_gbp_m"] = row.qoq_change_gbp_m
    d["qoq_change_pct"] = row.qoq_change_pct
    return d


@dataclass(frozen=True)
class EnergyTradeAnalysis:
    """Primary: CPA (08) Q2 YoY; secondary: SITC 3 fuels QoQ substitute."""

    focus_quarter: str
    cp_measure: str
    source_cpa_page: str
    source_trade_tables_page: str
    bulletin_url: str
    cpa08_file: str
    trade_tables_file: str
    cpa_crude_exports: CpaQuarterLevel
    cpa_crude_gas_imports: CpaQuarterLevel
    cpa_refined_imports: CpaQuarterLevel
    cpa_total_goods_exports: CpaQuarterLevel
    cpa_total_goods_imports: CpaQuarterLevel
    cpa_energy_trade_balance: dict[str, float]
    pdf_claim_check: tuple[dict[str, Any], ...]
    sitc3_fuels_substitute: dict[str, Any] | None
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "focus_quarter": self.focus_quarter,
            "cp_measure": self.cp_measure,
            "source_cpa_page": self.source_cpa_page,
            "source_trade_tables_page": self.source_trade_tables_page,
            "bulletin_url": self.bulletin_url,
            "cpa08_file": self.cpa08_file,
            "trade_tables_file": self.trade_tables_file,
            "cpa_crude_exports": _cpa_row_dict(self.cpa_crude_exports),
            "cpa_crude_gas_imports": _cpa_row_dict(self.cpa_crude_gas_imports),
            "cpa_refined_imports": _cpa_row_dict(self.cpa_refined_imports),
            "cpa_total_goods_exports": _cpa_row_dict(self.cpa_total_goods_exports),
            "cpa_total_goods_imports": _cpa_row_dict(self.cpa_total_goods_imports),
            "cpa_energy_trade_balance": self.cpa_energy_trade_balance,
            "original_pdf_claim_check": list(self.pdf_claim_check),
            "sitc3_fuels_substitute_qoq_only": self.sitc3_fuels_substitute,
            "notes": list(self.notes),
        }


def _cpa_quarter_indices(ws: Any) -> tuple[int, int]:
    for row in ws.iter_rows(max_row=8, values_only=True):
        if row and row[0] == "PRODUCT BY ACTIVITY":
            hdr = list(row)
            return hdr.index(COMPARE_QUARTER_PRIOR), hdr.index(COMPARE_QUARTER_CURRENT)
    raise ValueError("CPA quarter header row not found")


def _cpa_row(
    ws: Any, label: str, direction: str, i_prior: int, i_curr: int
) -> CpaQuarterLevel:
    for row in ws.iter_rows(max_row=400, values_only=True):
        if row and row[0] == label:
            prior = float(row[i_prior]) / 1000.0
            curr = float(row[i_curr]) / 1000.0
            sid = str(row[1]) if row[1] else ""
            return CpaQuarterLevel(label, direction, sid, round(prior, 3), round(curr, 3))
    raise ValueError(f"CPA row not found: {label!r}")


def _sum_cpa(ws: Any, labels: tuple[str, ...], idx: int) -> float:
    total = 0.0
    for label in labels:
        for row in ws.iter_rows(max_row=400, values_only=True):
            if row and row[0] == label:
                total += float(row[idx])
    return total / 1000.0


def _energy_balance_q(
    exp_ws: Any, imp_ws: Any, i_prior: int, i_curr: int
) -> tuple[float, float]:
    """Exports minus imports for CPA 06 + 19.2, £bn (repo definition)."""

    labels = (CPA_CRUDE_GAS_IMPORT, CPA_REFINED_IMPORT)
    prior_bal = _sum_cpa(exp_ws, labels, i_prior) - _sum_cpa(imp_ws, labels, i_prior)
    curr_bal = _sum_cpa(exp_ws, labels, i_curr) - _sum_cpa(imp_ws, labels, i_curr)
    return round(prior_bal, 3), round(curr_bal, 3)


def _pdf_checks(
    crude: CpaQuarterLevel,
    crude_gas_imp: CpaQuarterLevel,
    refined_imp: CpaQuarterLevel,
    goods_exp: CpaQuarterLevel,
    goods_imp: CpaQuarterLevel,
    bal_prior: float,
    bal_curr: float,
) -> tuple[dict[str, Any], ...]:
    imp_delta = goods_imp.yoy_change_gbp_b
    crude_gas_delta = crude_gas_imp.yoy_change_gbp_b
    energy_share = (
        round(crude_gas_delta / imp_delta * 100, 1) if imp_delta else None
    )
    return (
        {
            "claim": "Crude exports +109% YoY to £5.4bn (PDF)",
            "comparable_series": CPA_CRUDE_EXPORT,
            "recomputed_yoy_pct": crude.yoy_change_pct,
            "recomputed_current_q_gbp_b": crude.current_q_gbp_b,
            "validation": "not_validated_as_stated",
            "comment": "CPA 06.1 Q2 YoY differs on both % and level vs PDF wording.",
        },
        {
            "claim": "Crude+gas imports +35.8% YoY to £11.7bn (PDF)",
            "comparable_series": CPA_CRUDE_GAS_IMPORT,
            "recomputed_yoy_pct": crude_gas_imp.yoy_change_pct,
            "recomputed_current_q_gbp_b": crude_gas_imp.current_q_gbp_b,
            "validation": "close",
            "comment": "Level ~£11.68bn; YoY % ~36.6 vs PDF 35.8.",
        },
        {
            "claim": "Refined imports +64.8% YoY to £8.9bn (PDF)",
            "comparable_series": CPA_REFINED_IMPORT,
            "recomputed_yoy_pct": refined_imp.yoy_change_pct,
            "recomputed_current_q_gbp_b": refined_imp.current_q_gbp_b,
            "validation": "partial",
            "comment": "Level ~£9.24bn; YoY % higher than PDF 64.8%.",
        },
        {
            "claim": "Energy deficit £10.7bn, £2.8bn worse YoY (PDF)",
            "comparable_series": "CPA 06 + 19.2 exports minus imports (repo definition)",
            "recomputed_current_q_gbp_b": bal_curr,
            "recomputed_prior_q_gbp_b": bal_prior,
            "recomputed_yoy_change_gbp_b": round(bal_curr - bal_prior, 3),
            "validation": "not_validated_as_stated",
            "comment": "ONS bulletin may use a wider energy basket; not assumed correct.",
        },
        {
            "claim": "Energy +£6.6bn of +£15bn goods import growth, 44% (PDF)",
            "comparable_series": "CPA 06 import delta / total goods import delta",
            "recomputed_energy_import_delta_gbp_b": crude_gas_delta,
            "recomputed_total_goods_import_delta_gbp_b": imp_delta,
            "recomputed_share_pct": energy_share,
            "validation": "not_validated_as_stated",
            "comment": "Share ~20% on CPA 06 only; PDF energy scope unknown.",
        },
        {
            "claim": "Goods exports £101.7bn, imports £171bn (PDF)",
            "comparable_series": "CPA Total exports/imports Q2 2026",
            "recomputed_exports_gbp_b": goods_exp.current_q_gbp_b,
            "recomputed_imports_gbp_b": goods_imp.current_q_gbp_b,
            "validation": "close",
            "comment": "Imports match; exports differ (~£107.2bn CPA total exports Q2).",
        },
    )


def parse_cpa08_energy_trade(
    cpa_path: Path | str,
    *,
    trade_tables_path: Path | str | None = None,
    source_cpa_page: str = ONS_CPA08_PAGE,
    source_trade_tables_page: str = ONS_PUBLICATION_TABLES_PAGE,
    bulletin_url: str = ONS_TRADE_BULLETIN_JUNE_2026,
) -> EnergyTradeAnalysis:
    cpa = Path(cpa_path)
    wb = openpyxl.load_workbook(cpa, read_only=True, data_only=True)
    exp_ws = wb[SHEET_CPA_EXPORTS_Q]
    imp_ws = wb[SHEET_CPA_IMPORTS_Q]
    i_prior, i_curr = _cpa_quarter_indices(exp_ws)

    crude_exp = _cpa_row(exp_ws, CPA_CRUDE_EXPORT, "Exports", i_prior, i_curr)
    crude_gas_imp = _cpa_row(imp_ws, CPA_CRUDE_GAS_IMPORT, "Imports", i_prior, i_curr)
    refined_imp = _cpa_row(imp_ws, CPA_REFINED_IMPORT, "Imports", i_prior, i_curr)
    goods_exp = _cpa_row(exp_ws, CPA_TOTAL_EXPORTS, "Exports", i_prior, i_curr)
    goods_imp = _cpa_row(imp_ws, CPA_TOTAL_IMPORTS, "Imports", i_prior, i_curr)
    bal_prior, bal_curr = _energy_balance_q(exp_ws, imp_ws, i_prior, i_curr)
    wb.close()

    sitc_sub: dict[str, Any] | None = None
    trade_name = ""
    if trade_tables_path and Path(trade_tables_path).is_file():
        trade_name = Path(trade_tables_path).name
        sitc = _parse_sitc3_qoq(Path(trade_tables_path))
        sitc_sub = {
            "label": "SITC 3 Fuels substitute (Table 2A) — QoQ Q1→Q2 2026 only",
            "classification_note": "SITC ≠ CPA (08); CP prices only; not a PDF crude recreation.",
            "exports": _fuel_row_dict(sitc["exports"]),
            "imports": _fuel_row_dict(sitc["imports"]),
            "balance": _fuel_row_dict(sitc["balance"]),
        }

    return EnergyTradeAnalysis(
        focus_quarter="2026-Q2",
        cp_measure=(
            "Classification of Products by Activity (CPA 08); "
            "current prices (CP), seasonally adjusted; £m → £bn"
        ),
        source_cpa_page=source_cpa_page,
        source_trade_tables_page=source_trade_tables_page,
        bulletin_url=bulletin_url,
        cpa08_file=cpa.name,
        trade_tables_file=trade_name,
        cpa_crude_exports=crude_exp,
        cpa_crude_gas_imports=crude_gas_imp,
        cpa_refined_imports=refined_imp,
        cpa_total_goods_exports=goods_exp,
        cpa_total_goods_imports=goods_imp,
        cpa_energy_trade_balance={
            "definition": "CPA 06 + 19.2 exports minus imports (repo, not ONS headline)",
            "prior_q_gbp_b": bal_prior,
            "current_q_gbp_b": bal_curr,
            "yoy_change_gbp_b": round(bal_curr - bal_prior, 3),
        },
        pdf_claim_check=_pdf_checks(
            crude_exp, crude_gas_imp, refined_imp, goods_exp, goods_imp, bal_prior, bal_curr
        ),
        sitc3_fuels_substitute=sitc_sub,
        notes=(
            "Primary validation uses CPA (08) quarterly CP sheets 2 & 4.",
            "PDF YoY claims require the same CPA row and Q2 2025 vs Q2 2026.",
            "SITC 3 Fuels (publication Table 2A) is an explicit substitute for QoQ context only.",
            "Do not treat SITC % change as proof the PDF crude YoY claim is wrong.",
        ),
    )


def _load_header_and_indices(header_row: tuple[Any, ...]) -> tuple[list[Any], int, int]:
    header = list(header_row)
    return header, header.index("2026 Q1"), header.index("2026 Q2")


def _parse_sitc3_qoq(path: Path) -> dict[str, FuelQuarterRow]:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[SHEET_QUARTERLY_CP]
    header: list[Any] | None = None
    q1_i = q2_i = -1
    buckets: dict[str, tuple[Any, ...]] = {}
    for row in ws.iter_rows(max_row=600, values_only=True):
        if row[0] == "Series" and row[5] == "1997 Q1":
            header, q1_i, q2_i = _load_header_and_indices(row)
            continue
        if header is None:
            continue
        if (
            row[0] == "Trade in goods"
            and row[2]
            and "SITC 3 Fuels" in str(row[2])
            and row[3] == "Total World"
            and row[1] in ("Exports", "Imports", "Balance")
        ):
            buckets[str(row[1])] = row
    wb.close()
    if q1_i < 0 or len(buckets) < 3:
        raise ValueError("SITC 3 Fuels world rows not found in Quarterly CP sheet")

    def mk(key: str) -> FuelQuarterRow:
        r = buckets[key]
        return FuelQuarterRow(
            direction=str(r[1]),
            commodity=str(r[2]),
            area=str(r[3]),
            series_id=str(r[4]),
            q1_2026_gbp_m=round(float(r[q1_i]) / 1000.0, 3),
            q2_2026_gbp_m=round(float(r[q2_i]) / 1000.0, 3),
        )

    return {"exports": mk("Exports"), "imports": mk("Imports"), "balance": mk("Balance")}


def parse_quarterly_cp_xlsx(xlsx_path: Path | str, **kwargs: Any) -> EnergyTradeAnalysis:
    """Back-compat: requires CPA08 alongside trade tables when possible."""
    trade = Path(xlsx_path)
    cpa_default = trade.parent / "cpapublicationq22026august.xlsx"
    cpa = cpa_default if cpa_default.is_file() else None
    if cpa is None:
        raise ValueError(
            "CPA (08) xlsx required for energy trade validation; "
            f"expected {cpa_default}"
        )
    return parse_cpa08_energy_trade(cpa, trade_tables_path=trade, **kwargs)
