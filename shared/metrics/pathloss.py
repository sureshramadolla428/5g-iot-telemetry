"""Path loss: FSPL (three forms), log-distance, TR 38.901 UMa LOS PL1/PL2."""

from __future__ import annotations

import math

from metrics.constants import C_MPS


def fspl_db_from_m_hz(distance_m: float, freq_hz: float) -> float:
    """FSPL_dB = 20 log10(d_m) + 20 log10(f_Hz) - 147.55."""
    if distance_m <= 0.0 or freq_hz <= 0.0:
        raise ValueError("distance and frequency must be > 0")
    return 20.0 * math.log10(distance_m) + 20.0 * math.log10(freq_hz) - 147.55


def fspl_db_from_km_ghz(distance_km: float, freq_ghz: float) -> float:
    """FSPL_dB = 20 log10(d_km) + 20 log10(f_GHz) + 92.45."""
    if distance_km <= 0.0 or freq_ghz <= 0.0:
        raise ValueError("distance and frequency must be > 0")
    return 20.0 * math.log10(distance_km) + 20.0 * math.log10(freq_ghz) + 92.45


def fspl_db_from_km_mhz(distance_km: float, freq_mhz: float) -> float:
    """FSPL_dB = 20 log10(d_km) + 20 log10(f_MHz) + 32.44."""
    if distance_km <= 0.0 or freq_mhz <= 0.0:
        raise ValueError("distance and frequency must be > 0")
    return 20.0 * math.log10(distance_km) + 20.0 * math.log10(freq_mhz) + 32.44


def log_distance_pl_db(
    distance_m: float,
    d0_m: float,
    pl0_db: float,
    exponent: float,
    shadow_db: float = 0.0,
) -> float:
    if distance_m <= 0.0 or d0_m <= 0.0:
        raise ValueError("distances must be > 0")
    return pl0_db + 10.0 * exponent * math.log10(distance_m / d0_m) + shadow_db


def uma_breakpoint_m(h_bs_m: float, h_ut_m: float, freq_hz: float) -> float:
    """d_BP' = 4 * h_BS' * h_UT' * f_c / c with h' = h - 1 m (TR 38.901)."""
    h_bs_p = h_bs_m - 1.0
    h_ut_p = h_ut_m - 1.0
    if h_bs_p <= 0.0 or h_ut_p <= 0.0:
        raise ValueError("UMa effective heights h-1 m must be > 0")
    return 4.0 * h_bs_p * h_ut_p * freq_hz / C_MPS


def uma_los_pl_db(
    d_2d_m: float,
    h_bs_m: float,
    h_ut_m: float,
    freq_ghz: float,
) -> tuple[float, str, float]:
    """TR 38.901 Table 7.4.1-1 UMa LOS PL1/PL2.

    Returns (PL_dB, segment, d_BP'_m).
    PL1: 10 m <= d_2D <= d_BP'
      28.0 + 22 log10(d_3D) + 20 log10(f_c)
    PL2: d_BP' <= d_2D <= 5 km
      28.0 + 40 log10(d_3D) + 20 log10(f_c)
      - 9 log10((d_BP')^2 + (h_BS - h_UT)^2)
    """
    if freq_ghz <= 0.0:
        raise ValueError("freq_ghz must be > 0")
    freq_hz = freq_ghz * 1e9
    d_bp = uma_breakpoint_m(h_bs_m, h_ut_m, freq_hz)
    d_3d = math.sqrt(d_2d_m**2 + (h_bs_m - h_ut_m) ** 2)
    if d_2d_m < 10.0:
        raise ValueError("UMa LOS not defined for d_2D < 10 m")
    if d_2d_m <= d_bp:
        pl = 28.0 + 22.0 * math.log10(d_3d) + 20.0 * math.log10(freq_ghz)
        return pl, "PL1", d_bp
    if d_2d_m > 5000.0:
        raise ValueError("UMa LOS PL2 not defined for d_2D > 5 km")
    pl = (
        28.0
        + 40.0 * math.log10(d_3d)
        + 20.0 * math.log10(freq_ghz)
        - 9.0 * math.log10(d_bp**2 + (h_bs_m - h_ut_m) ** 2)
    )
    return pl, "PL2", d_bp
