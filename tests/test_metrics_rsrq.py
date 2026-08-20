from __future__ import annotations

import math

import pytest

from metrics.convert import dbm_to_mw
from metrics.ts38215 import modeled_rsrp_bundle, rsrq_db, rsrq_linear


def test_rsrq_identity():
    rsrp_dbm, rssi_dbm, n_prb = -90.0, -65.0, 51
    db = rsrq_db(rsrp_dbm, rssi_dbm, n_prb)
    expected = rsrp_dbm - rssi_dbm + 10.0 * math.log10(n_prb)
    assert db == pytest.approx(expected)
    lin = rsrq_linear(dbm_to_mw(rsrp_dbm), dbm_to_mw(rssi_dbm), n_prb)
    assert 10.0 * math.log10(lin) == pytest.approx(db, abs=1e-9)


def test_rsrp_is_per_re_not_wideband_prx():
    n_prb = 51
    p_rx = -65.0
    bundle = modeled_rsrp_bundle(p_rx_dbm=p_rx, n_prb=n_prb, sinr_db_value=12.0)
    expected = p_rx - 10.0 * math.log10(12 * n_prb)
    assert bundle["rsrp_dbm"] == pytest.approx(expected)
    assert bundle["rsrp_dbm"] < p_rx - 20.0

