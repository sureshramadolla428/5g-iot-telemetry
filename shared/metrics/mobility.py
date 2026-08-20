"""Doppler, coherence, Haversine, L3 filter (TS 38.331), A3 HO events."""

from __future__ import annotations

import math

from metrics.constants import C_MPS, R_E_M


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    rlat1, rlon1, rlat2, rlon2 = map(math.radians, (lat1, lon1, lat2, lon2))
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return 2 * R_E_M * math.asin(min(1.0, math.sqrt(a)))


def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlon = math.radians(lon2 - lon1)
    x = math.sin(dlon) * math.cos(rlat2)
    y = math.cos(rlat1) * math.sin(rlat2) - math.sin(rlat1) * math.cos(rlat2) * math.cos(dlon)
    return (math.degrees(math.atan2(x, y)) + 360.0) % 360.0


def speed_mps(
    lat1: float, lon1: float, lat2: float, lon2: float, dt_s: float
) -> float:
    if dt_s <= 0.0:
        raise ValueError("dt_s must be > 0")
    return haversine_m(lat1, lon1, lat2, lon2) / dt_s


def doppler_hz(velocity_mps: float, freq_hz: float, angle_rad: float) -> float:
    """f_d = (v/c) * f * cos(theta). theta=0 is radial approach (positive)."""
    return (velocity_mps / C_MPS) * freq_hz * math.cos(angle_rad)


def coherence_time_s(fd_max_hz: float) -> float:
    """Clarke: Tc ≈ 0.423 / f_dmax."""
    if fd_max_hz <= 0.0:
        raise ValueError("f_dmax must be > 0")
    return 0.423 / fd_max_hz


def coherence_bandwidth_hz(delay_spread_s: float) -> float:
    """Bc ≈ 1 / (2 π σ_τ) (50% correlation rule of thumb)."""
    if delay_spread_s <= 0.0:
        raise ValueError("delay spread must be > 0")
    return 1.0 / (2.0 * math.pi * delay_spread_s)


def scs_doppler_warning(fd_hz: float, scs_hz: float, fraction: float = 0.1) -> bool:
    """True when |Doppler| is large vs subcarrier spacing (numerology risk)."""
    return abs(fd_hz) > fraction * scs_hz


def l3_filter_coeff(k: int) -> float:
    """TS 38.331: a = 1/2^(k/4)."""
    return 0.5 ** (k / 4.0)


def l3_filter_step(prev: float | None, meas: float, k: int) -> float:
    """F_n = (1-a) F_{n-1} + a M_n; F_0 = M_0."""
    if prev is None:
        return meas
    a = l3_filter_coeff(k)
    return (1.0 - a) * prev + a * meas


def a3_entering(
    mn_dbm: float,
    mp_dbm: float,
    *,
    ofn: float = 0.0,
    ocn: float = 0.0,
    ofp: float = 0.0,
    ocp: float = 0.0,
    hys: float = 1.0,
    off: float = 3.0,
) -> bool:
    """TS 38.331 A3 entering: Mn+Ofn+Ocn-Hys > Mp+Ofp+Ocp+Off."""
    return (mn_dbm + ofn + ocn - hys) > (mp_dbm + ofp + ocp + off)
