from __future__ import annotations

import math

import pytest

from metrics.convert import avg_db, db_to_lin_power, dbm_to_mw, mw_to_dbm


def test_dbm_mw_roundtrip():
    assert abs(mw_to_dbm(dbm_to_mw(-90.0)) + 90.0) < 1e-9
    assert abs(dbm_to_mw(0.0) - 1.0) < 1e-12


def test_avg_db_uses_linear_power_not_arithmetic():
    samples = [-80.0, -90.0, -100.0]
    arithmetic = sum(samples) / 3.0
    linear = avg_db(samples)
    assert linear != pytest.approx(arithmetic)
    expected = 10 * math.log10(sum(db_to_lin_power(s) for s in samples) / 3)
    assert linear == pytest.approx(expected)


def test_avg_db_empty_rejected():
    with pytest.raises(ValueError):
        avg_db([])
