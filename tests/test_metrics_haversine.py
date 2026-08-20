from __future__ import annotations

import pytest

from metrics.mobility import bearing_deg, haversine_m


def test_haversine_one_degree_equator():
    d = haversine_m(0.0, 0.0, 0.0, 1.0)
    assert d == pytest.approx(111194.93, rel=1e-3)


def test_haversine_zero():
    assert haversine_m(37.77, -122.42, 37.77, -122.42) == pytest.approx(0.0, abs=1e-6)


def test_bearing_east():
    b = bearing_deg(0.0, 0.0, 0.0, 1.0)
    assert b == pytest.approx(90.0, abs=0.5)
