"""
Application configuration: paths, DuckDB tuning, and official UK open dataset URLs.

Dataset links point to open government data suitable for macro-economic analysis.
URLs may change when publishers update their sites; see README for how to override.
"""

from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass, field
from typing import Mapping


def _default_project_root() -> Path:
    # src/config.py -> repo root is parent of src/
    return Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Paths:
    """Filesystem locations for cache, database, and exports."""

    project_root: Path = field(default_factory=_default_project_root)
    data_cache_dir: Path | None = None
    duckdb_path: str | None = ":memory:"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "data_cache_dir",
            self.data_cache_dir
            if self.data_cache_dir is not None
            else self.project_root / "data" / "cache",
        )

    @property
    def parquet_dir(self) -> Path:
        return self.data_cache_dir / "parquet"

    @property
    def export_dir(self) -> Path:
        return self.project_root / "data" / "exports"


@dataclass(frozen=True)
class DuckDBSettings:
    """DuckDB performance and resource limits."""

    threads: int = 4
    memory_limit: str = "2GB"
    enable_object_cache: bool = True
    preserve_insertion_order: bool = False


@dataclass(frozen=True)
class HTTPSettings:
    """HTTP client defaults for dataset downloads."""

    timeout_seconds: float = 60.0
    max_retries: int = 3
    user_agent: str = "uk-macro-analytics-engine/0.1 (+https://github.com/)"

    @property
    def headers(self) -> dict[str, str]:
        return {"User-Agent": self.user_agent, "Accept": "text/csv,*/*"}


@dataclass(frozen=True)
class DatasetSpec:
    """Named remote dataset with expected CSV columns after normalization."""

    key: str
    description: str
    url: str
    expected_columns: tuple[str, ...]
    date_column: str | None = None
    value_columns: tuple[str, ...] = ()


# Official / open UK macro data sources (CSV where possible).
# HM Treasury Public Sector Finances bulletin tables (machine-readable on GOV.UK).
# ONS: Consumer Prices Index including owner occupiers' housing costs (CPIH) — monthly series.
DATASETS: Mapping[str, DatasetSpec] = {
    "ons_cpih_monthly": DatasetSpec(
        key="ons_cpih_monthly",
        description=(
            "ONS CPIH monthly index (all items); CSV from ONS time-series generator."
        ),
        url=(
            "https://www.ons.gov.uk/generator?"
            "format=csv&uri=/economy/inflationandpriceindices/timeseries/l522/mm23"
        ),
        expected_columns=("time", "value"),
        date_column="time",
        value_columns=("value",),
    ),
    "ons_psnb_monthly": DatasetSpec(
        key="ons_psnb_monthly",
        description=(
            "ONS public sector net borrowing, excluding public sector banks — monthly, £ million "
            "(series DZLS / dataset PUSF)."
        ),
        url=(
            "https://www.ons.gov.uk/generator?"
            "format=csv&uri=/economy/governmentpublicsectorandtaxes/publicsectorfinance"
            "/timeseries/dzls/pusf"
        ),
        # After normalization + parsing: one row per month with borrowing in £m (column `value`).
        expected_columns=("time", "value"),
        date_column="time",
        value_columns=("value",),
    ),
}


@dataclass(frozen=True)
class Settings:
    """Top-level settings bag."""

    paths: Paths = field(default_factory=Paths)
    duckdb: DuckDBSettings = field(default_factory=DuckDBSettings)
    http: HTTPSettings = field(default_factory=HTTPSettings)
    datasets: Mapping[str, DatasetSpec] = field(default_factory=lambda: DATASETS)


def get_settings() -> Settings:
    return Settings()
