"""Pydantic models matching config/payload.schema.json."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from metrics.constants import MODELED_DISCLAIMER, SCHEMA_VERSION, SOURCE_MEASURED, SOURCE_MODELED

StatusLiteral = Literal["online", "offline", "degraded"]
SourceLiteral = Literal["modeled", "measured"]


class RadioKpis(BaseModel):
    """RF quantities. In this lab they are always modeled (no UERANSIM PHY)."""

    model_config = ConfigDict(extra="ignore")

    source: SourceLiteral = SOURCE_MODELED
    disclaimer: str = MODELED_DISCLAIMER
    model: str | None = None
    rsrp_dbm: float | None = None
    rsrp_mw: float | None = None
    rssi_dbm: float | None = None
    rssi_mw: float | None = None
    rsrq_db: float | None = None
    ss_sinr_db: float | None = None
    sinr_db: float | None = None
    snr_db: float | None = None
    cqi: int | None = Field(default=None, ge=0, le=15)
    mcs: int | None = Field(default=None, ge=0, le=28)
    tbs_bits: int | None = None
    path_loss_db: float | None = None
    p_rx_dbm: float | None = None
    eirp_dbm: float | None = None
    doppler_hz: float | None = None
    uma_segment: str | None = None
    d_bp_prime_m: float | None = None
    residual_bler: float | None = None
    t_prop_ms: float | None = None
    l_up_ms: float | None = None
    latency_budget_pct: float | None = None
    scs_doppler_warning: bool | None = None
    ss_rsrp_report: int | None = None
    n_prb: int | None = None

    @model_validator(mode="after")
    def phy_must_be_modeled(self) -> RadioKpis:
        phy = any(
            v is not None
            for v in (
                self.rsrp_dbm,
                self.rsrq_db,
                self.ss_sinr_db,
                self.sinr_db,
                self.cqi,
                self.mcs,
            )
        )
        if phy and self.source == SOURCE_MEASURED:
            raise ValueError("PHY KPIs cannot be source=measured (UERANSIM has no radio PHY)")
        if phy and MODELED_DISCLAIMER not in self.disclaimer:
            raise ValueError("modeled PHY KPIs require the visible disclaimer")
        return self


class MeasuredKpis(BaseModel):
    source: SourceLiteral = SOURCE_MEASURED
    rtt_ms: float | None = None
    owd_ms: float | None = None
    jitter_rfc3550_ms: float | None = None
    iface_rx_bytes: int | None = None
    iface_tx_bytes: int | None = None
    iface_rx_packets: int | None = None
    iface_tx_packets: int | None = None
    speed_mps: float | None = None
    bearing_deg: float | None = None


class EchoPayload(BaseModel):
    device_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9._:-]+$")
    role: Literal["ping", "pong"]
    sequence_number: int = Field(ge=0)
    t_tx_unix_ms: float
    t_rx_unix_ms: float | None = None


class TelemetryPayload(BaseModel):
    device_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9._:-]+$")
    timestamp: datetime
    temperature: float = Field(ge=-40, le=85)
    humidity: float = Field(ge=0, le=100)
    battery: float = Field(ge=0, le=100)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    status: StatusLiteral
    source_ip: str | None = None
    schema_version: str = SCHEMA_VERSION
    sequence_number: int | None = Field(default=None, ge=0)
    radio: RadioKpis | None = None
    measured: MeasuredKpis | None = None

    @field_validator("timestamp")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware UTC")
        return value.astimezone(UTC)

    def to_iso(self) -> str:
        return self.timestamp.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class DeviceStatusPayload(BaseModel):
    device_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9._:-]+$")
    timestamp: datetime
    status: StatusLiteral
    detail: str | None = None

    @field_validator("timestamp")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware UTC")
        return value.astimezone(UTC)
