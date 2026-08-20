from __future__ import annotations

import pytest

from metrics.constants import GEO_ALTITUDE_KM
from metrics.ntn import geo_nadir_one_way_s, ntn_snapshot, slant_range_m


def test_geo_nadir_delay_about_119ms():
    ms = geo_nadir_one_way_s() * 1000.0
    assert ms == pytest.approx(119.35, abs=1.0)


def test_ntn_geo_snapshot_delay_band():
    cfg = {
        "orbit": "GEO",
        "altitude_km": GEO_ALTITUDE_KM,
        "elevation_deg": 90.0,
        "freq_hz": 20e9,
    }
    snap = ntn_snapshot(cfg)
    assert snap["source"] == "modeled"
    assert "not radio-measured" in snap["disclaimer"]
    assert snap["t_prop_one_way_ms"] == pytest.approx(119.35, abs=1.0)


def test_leo_nadir_delay_band():
    d = slant_range_m(550_000.0, 90.0)
    ms = 1000.0 * d / 299_792_458.0
    assert 1.5 < ms < 3.0
