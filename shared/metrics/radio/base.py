"""Swappable radio model interface. SDR/COTS/srsRAN can implement this later."""

from __future__ import annotations

from typing import Any, Protocol

from metrics.constants import MODELED_DISCLAIMER, SOURCE_MEASURED, SOURCE_MODELED


class RadioModel(Protocol):
    name: str

    def snapshot(self, cfg: dict[str, Any]) -> dict[str, Any]:
        """Return KPI dict. Must include source and disclaimer for RF quantities."""
        ...


def assert_modeled_rf(kpi: dict[str, Any]) -> None:
    """Refuse to treat UERANSIM-era RF as measured."""
    if kpi.get("rsrp_dbm") is None and kpi.get("ss_sinr_db") is None:
        return
    if kpi.get("source") != SOURCE_MODELED:
        raise ValueError("RSRP/RSRQ/SINR/CQI must be source='modeled' (no PHY on UERANSIM)")
    if MODELED_DISCLAIMER not in str(kpi.get("disclaimer", "")):
        raise ValueError("modeled RF KPIs must carry the visible disclaimer")


def forbid_measured_phy(source: str, has_phy_fields: bool) -> None:
    if has_phy_fields and source == SOURCE_MEASURED:
        raise ValueError("cannot tag PHY fields as measured in this lab")
