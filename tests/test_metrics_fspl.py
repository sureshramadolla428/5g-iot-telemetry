from __future__ import annotations

import pytest

from metrics.pathloss import fspl_db_from_km_ghz, fspl_db_from_km_mhz, fspl_db_from_m_hz


def test_fspl_three_forms_agree_1km_1ghz():
    a = fspl_db_from_km_mhz(1.0, 1000.0)
    b = fspl_db_from_km_ghz(1.0, 1.0)
    c = fspl_db_from_m_hz(1000.0, 1e9)
    assert a == pytest.approx(92.44, abs=0.05)
    assert a == pytest.approx(b, abs=0.05)
    assert a == pytest.approx(c, abs=0.05)
