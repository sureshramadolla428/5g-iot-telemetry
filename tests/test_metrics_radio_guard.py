from __future__ import annotations

import pytest
from pydantic import ValidationError

from iot_schema.payload import RadioKpis
from iot_schema.topics import echo_topic, parse_device_topic
from metrics.constants import MODELED_DISCLAIMER
from metrics.pathloss import uma_breakpoint_m, uma_los_pl_db
from metrics.radio.factory import build_radio_model


def test_radio_measured_phy_rejected():
    with pytest.raises(ValidationError):
        RadioKpis(source="measured", rsrp_dbm=-90.0, disclaimer=MODELED_DISCLAIMER)


def test_radio_modeled_ok():
    r = RadioKpis(source="modeled", rsrp_dbm=-90.0, rsrp_mw=1e-9)
    assert "not radio-measured" in r.disclaimer


def test_echo_topic():
    assert echo_topic("iot-001") == "iot/devices/iot-001/echo"
    device_id, kind = parse_device_topic("iot/devices/iot-001/echo")
    assert device_id == "iot-001"
    assert kind == "echo"


def test_uma_breakpoint_and_pl1():
    d_bp = uma_breakpoint_m(25.0, 1.5, 3.5e9)
    assert d_bp > 0.0
    pl, seg, bp = uma_los_pl_db(100.0, 25.0, 1.5, 3.5)
    assert seg == "PL1"
    assert bp == pytest.approx(d_bp)
    assert pl > 0.0


def test_terrestrial_snapshot_is_modeled():
    model = build_radio_model({"profile": "terrestrial"})
    snap = model.snapshot(
        {
            "freq_hz": 3.5e9,
            "bandwidth_hz": 20e6,
            "distance_2d_m": 150.0,
            "h_bs_m": 25.0,
            "h_ut_m": 1.5,
        }
    )
    assert snap["source"] == "modeled"
    assert "not radio-measured" in snap["disclaimer"]
    assert snap["rsrp_mw"] > 0


def test_default_model_is_terrestrial():
    model = build_radio_model({"profile": "terrestrial", "enable_ntn": False})
    assert model.name == "terrestrial_uma"


def test_ntn_flag_selects_ntn():
    assert build_radio_model({"enable_ntn": True}).name == "ntn"


def test_a2g_flag_selects_a2g():
    assert build_radio_model({"enable_a2g": True}).name == "a2g"


def test_both_flags_rejected():
    with pytest.raises(ValueError):
        build_radio_model({"enable_ntn": True, "enable_a2g": True})
