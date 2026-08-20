from __future__ import annotations

from metrics.constants import C_MPS, GEO_ALTITUDE_KM, K_FACTOR, N0_DBM_PER_HZ, R_E_KM, T0_K


def test_constants():
    assert C_MPS == 299_792_458.0
    assert abs(N0_DBM_PER_HZ - (-174.0)) < 1e-9
    assert T0_K == 290.0
    assert R_E_KM == 6371.0
    assert K_FACTOR == 4.0 / 3.0
    assert GEO_ALTITUDE_KM == 35786.0
