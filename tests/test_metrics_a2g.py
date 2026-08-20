from __future__ import annotations

import pytest

from metrics.a2g import HorizonError, a2g_snapshot, aircraft_doppler_hz, radio_horizon_m


def test_radio_horizon_positive():
    h = radio_horizon_m(300.0, 1.5)
    assert h > 50_000.0


def test_a2g_refuses_beyond_horizon():
    cfg = {
        "freq_hz": 3.5e9,
        "aircraft_alt_m": 50.0,
        "gs_alt_m": 1.5,
        "along_track_m": 1_000_000.0,
        "allow_beyond_horizon": False,
    }
    with pytest.raises(HorizonError):
        a2g_snapshot(cfg)


def test_a2g_allow_beyond_horizon():
    cfg = {
        "freq_hz": 3.5e9,
        "aircraft_alt_m": 50.0,
        "gs_alt_m": 1.5,
        "along_track_m": 1_000_000.0,
        "allow_beyond_horizon": True,
    }
    snap = a2g_snapshot(cfg)
    assert snap["beyond_horizon"] is True
    assert snap["source"] == "modeled"


def test_doppler_peak_positive_on_approach_zero_overhead():
    f = 3.5e9
    v = 70.0
    h = 300.0
    approach = aircraft_doppler_hz(-5000.0, h, v, f)
    overhead = aircraft_doppler_hz(0.0, h, v, f)
    departure = aircraft_doppler_hz(5000.0, h, v, f)
    assert approach > 0.0
    assert overhead == pytest.approx(0.0, abs=1e-9)
    assert departure < 0.0
