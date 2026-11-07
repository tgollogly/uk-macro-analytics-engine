"""UK trade in goods — fuels (SITC 3), quarterly current prices from ONS tables (rebuilt)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import openpyxl

ONS_PUBLICATION_TABLES_PAGE = (
    "https://www.ons.gov.uk/economy/nationalaccounts/balanceofpayments/"
    "datasets/uktradegoodsandservicespublicationtables/current"
)
ONS_TRADE_BULLETIN_JUNE_2026 = (
    "https://www.ons.gov.uk/economy/nationalaccounts/balanceofpayments/bulletins/uktrade/june2026"
)
DEFAULT_XLSX_URL = (
    "https://www.ons.gov.uk/file?uri=/economy/nationalaccounts/balanceofpayments/"
    "datasets/uktradegoodsandservicespublicationtables/current/"
    "tradepublicationtables2026aug.xlsx"
)
SHEET_QUARTERLY_CP = "2 - Quarterly CP"


@dataclass(frozen=True)
class FuelQuarterRow:
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
class EnergyTradeQuarterlyCP:
    period: str
    measure: str
    source_page: str
    bulletin_url: str
    xlsx_file: str
    fuels_exports_world: FuelQuarterRow
    fuels_imports_world: FuelQuarterRow
    fuels_balance_world: FuelQuarterRow
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "period": self.period,
            "measure": self.measure,
            "source_page": self.source_page,
            "bulletin_url": self.bulletin_url,
            "xlsx_file": self.xlsx_file,
            "fuels_exports_world": _fuel_row_dict(self.fuels_exports_world),
            "fuels_imports_world": _fuel_row_dict(self.fuels_imports_world),
            "fuels_balance_world": _fuel_row_dict(self.fuels_balance_world),
            "notes": list(self.notes),
        }


def _load_header_and_indices(header_row: tuple[Any, ...]) -> tuple[list[Any], int, int]:
    header = list(header_row)
    return header, header.index("2026 Q1"), header.index("2026 Q2")


def parse_quarterly_cp_xlsx(
    xlsx_path: Path | str,
    *,
    source_page: str = ONS_PUBLICATION_TABLES_PAGE,
    bulletin_url: str = ONS_TRADE_BULLETIN_JUNE_2026,
) -> EnergyTradeQuarterlyCP:
    path = Path(xlsx_path)
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

    return EnergyTradeQuarterlyCP(
        period="2026-Q2",
        measure="Current prices (CPA), seasonally adjusted, £ million in table → £ billion here",
        source_page=source_page,
        bulletin_url=bulletin_url,
        xlsx_file=path.name,
        fuels_exports_world=mk("Exports"),
        fuels_imports_world=mk("Imports"),
        fuels_balance_world=mk("Balance"),
        notes=(
            "Rebuilt Nov 2026 from ONS publication tables worksheet '2 - Quarterly CP' (table 2A).",
            "SITC 3 Fuels aggregates mineral fuels; not an official 'energy balance' total.",
            "QoQ compares Q2 2026 vs Q1 2026 — not bulletin country/commodity deltas.",
            "Do not mix current price (value) with chained volume (CVM) without labelling.",
        ),
    )
