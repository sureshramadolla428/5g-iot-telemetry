from __future__ import annotations

import json
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from iot_schema.payload import RadioKpis
from iot_schema.rows import attach_rfc3550_jitter, telemetry_sql_tuple
from iot_schema.telemetry import DeviceState, snapshot_payload, step_random_walk
from metrics.latency import Rfc3550Jitter
from metrics.radio.factory import build_radio_model, load_radio_config

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "dashboard" / "dashboards" / "iot-kpis.json"


def test_terrestrial_snapshot_validates_and_flattens():
    cfg = load_radio_config(ROOT / "config" / "radio_model.yaml")
    model = build_radio_model(cfg)
    radio = RadioKpis.model_validate(model.snapshot(cfg))
    assert radio.source == "modeled"
    assert "not radio-measured" in radio.disclaimer
    assert radio.rsrp_dbm is not None
    assert radio.rsrp_mw is not None
    assert radio.sinr_db is not None
    assert radio.cqi is not None

    state = DeviceState(device_id="iot-001")
    step_random_walk(state, random.Random(1))
    payload = snapshot_payload(state, radio=radio)
    ingested = payload.timestamp + timedelta(milliseconds=12.5)
    tup = telemetry_sql_tuple(payload, ingested_at=ingested)
    assert tup[1] == "iot-001"
    assert tup[12] == "modeled"
    assert tup[14] == radio.rsrp_dbm
    assert tup[15] == radio.rsrp_mw
    assert tup[19] == radio.sinr_db
    assert tup[21] == radio.cqi
    assert tup[-1] == pytest.approx(12.5)


def test_ingest_lag_is_receive_minus_device_timestamp():
    state = DeviceState(device_id="iot-002")
    payload = snapshot_payload(state)
    ingested = payload.timestamp + timedelta(milliseconds=40)
    tup = telemetry_sql_tuple(payload, ingested_at=ingested)
    assert tup[-1] == 40.0


def test_rsrp_mw_filled_from_dbm():
    state = DeviceState(device_id="iot-001")
    payload = snapshot_payload(
        state,
        radio={"source": "modeled", "rsrp_dbm": -80.0, "sinr_db": 10.0, "cqi": 7},
    )
    tup = telemetry_sql_tuple(payload)
    assert tup[14] == -80.0
    assert tup[15] is not None and tup[15] > 0
    assert tup[19] == 10.0
    assert tup[21] == 7


def test_sinr_falls_back_to_ss_sinr():
    state = DeviceState(device_id="iot-001")
    payload = snapshot_payload(
        state,
        radio={"source": "modeled", "rsrp_dbm": -90.0, "ss_sinr_db": 5.5},
    )
    tup = telemetry_sql_tuple(payload)
    assert tup[19] == 5.5


def test_rfc3550_jitter_stored_after_second_sample():
    tracker = Rfc3550Jitter()
    t0 = datetime.now(UTC)
    first = snapshot_payload(DeviceState(device_id="iot-001"))
    first.timestamp = t0
    attach_rfc3550_jitter(first, tracker, t0 + timedelta(milliseconds=10))
    assert first.measured is not None
    assert first.measured.jitter_rfc3550_ms == 0.0

    second = snapshot_payload(DeviceState(device_id="iot-001"))
    second.timestamp = t0 + timedelta(milliseconds=2000)
    attach_rfc3550_jitter(second, tracker, t0 + timedelta(milliseconds=2030))
    assert second.measured.jitter_rfc3550_ms is not None
    tup = telemetry_sql_tuple(second, ingested_at=t0 + timedelta(milliseconds=2030))
    assert tup[31] == second.measured.jitter_rfc3550_ms


def test_kpi_dashboard_queries_telemetry_columns():
    dash = json.loads(DASHBOARD.read_text(encoding="utf-8"))
    sql = " ".join(
        t["rawSql"] for p in dash["panels"] if "targets" in p for t in p["targets"]
    )
    assert "FROM telemetry" in sql
    assert "v_kpi_modeled" not in sql
    assert "v_kpi_measured" not in sql
    for col in (
        "rsrp_dbm",
        "rsrq_db",
        "sinr_db",
        "cqi",
        "rsrp_mw",
        "ingest_lag_ms",
        "jitter_rfc3550_ms",
        "radio_source",
    ):
        assert col in sql
    titles = [p["title"] for p in dash["panels"]]
    modeled = [
        t for t in titles if "RSRP" in t or "RSRQ" in t or "SINR" in t or t.startswith("CQI")
    ]
    for title in modeled:
        assert "modeled" in title.lower()
