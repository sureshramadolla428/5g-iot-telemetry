"""Flatten telemetry payload for Timescale inserts (mirrors SQL columns)."""

from __future__ import annotations

from datetime import UTC, datetime

from iot_schema.payload import MeasuredKpis, TelemetryPayload
from metrics.convert import dbm_to_mw
from metrics.latency import Rfc3550Jitter


def _mw(dbm: float | None, mw: float | None) -> float | None:
    if mw is not None and mw > 0.0:
        return mw
    if dbm is None:
        return None
    return dbm_to_mw(dbm)


def attach_rfc3550_jitter(
    row: TelemetryPayload,
    tracker: Rfc3550Jitter,
    received_at: datetime | None = None,
) -> TelemetryPayload:
    """RFC 3550 jitter from device timestamp (S) and consumer receive time (R)."""
    recv = received_at or datetime.now(UTC)
    send_ms = row.timestamp.timestamp() * 1000.0
    recv_ms = recv.timestamp() * 1000.0
    jitter = tracker.update(send_ms, recv_ms)
    meas = row.measured or MeasuredKpis()
    row.measured = meas.model_copy(update={"jitter_rfc3550_ms": jitter})
    return row


def telemetry_sql_tuple(row: TelemetryPayload, ingested_at: datetime | None = None) -> tuple:
    ingested = ingested_at or datetime.now(UTC)
    lag_ms = (ingested - row.timestamp).total_seconds() * 1000.0
    radio = row.radio
    meas = row.measured
    rsrp_dbm = radio.rsrp_dbm if radio else None
    rssi_dbm = radio.rssi_dbm if radio else None
    sinr = None
    if radio is not None:
        sinr = radio.sinr_db if radio.sinr_db is not None else radio.ss_sinr_db
    return (
        row.timestamp,
        row.device_id,
        row.temperature,
        row.humidity,
        row.battery,
        row.latitude,
        row.longitude,
        row.status,
        row.source_ip,
        ingested,
        row.schema_version,
        row.sequence_number,
        radio.source if radio else None,
        radio.disclaimer if radio else None,
        rsrp_dbm,
        _mw(rsrp_dbm, radio.rsrp_mw if radio else None),
        rssi_dbm,
        _mw(rssi_dbm, radio.rssi_mw if radio else None),
        radio.rsrq_db if radio else None,
        sinr,
        radio.snr_db if radio else None,
        radio.cqi if radio else None,
        radio.mcs if radio else None,
        radio.tbs_bits if radio else None,
        radio.path_loss_db if radio else None,
        radio.p_rx_dbm if radio else None,
        radio.doppler_hz if radio else None,
        radio.l_up_ms if radio else None,
        radio.latency_budget_pct if radio else None,
        meas.rtt_ms if meas else None,
        meas.owd_ms if meas else None,
        meas.jitter_rfc3550_ms if meas else None,
        meas.iface_rx_bytes if meas else None,
        meas.iface_tx_bytes if meas else None,
        lag_ms,
    )
