"""A2G geometry and radio (modeled). Does not modify any A2G lab project.

Assumptions where the originating spec was truncated after
'Peak positive at approach, zero at over[head]':
- Doppler uses along-track x with aircraft flying +x; f_d = -(v/c)*f*(x/r)
  so approach (x<0) is peak positive, overhead (x=0) is zero, departure negative.
- Two-ray uses a simple dielectric reflection on flat Earth.
- Fresnel 60% clearance is a planning check, not a measurement.
- Radio horizon uses 4/3 Earth; links beyond horizon are refused unless
  allow_beyond_horizon is set (still modeled, never measured).
"""

from __future__ import annotations

import math

from metrics.constants import C_MPS, K_FACTOR, MODELED_DISCLAIMER, R_E_M, SOURCE_MODELED
from metrics.pathloss import fspl_db_from_m_hz


class HorizonError(ValueError):
    """Raised when the A2G path is beyond radio horizon."""


def radio_horizon_m(h1_m: float, h2_m: float, k_factor: float = K_FACTOR) -> float:
    """d = sqrt(2 k R_e h1) + sqrt(2 k R_e h2)."""
    if h1_m < 0.0 or h2_m < 0.0:
        raise ValueError("heights must be >= 0")
    return math.sqrt(2.0 * k_factor * R_E_M * h1_m) + math.sqrt(2.0 * k_factor * R_E_M * h2_m)


def slant_range_m(ground_range_m: float, h_ac_m: float, h_gs_m: float = 0.0) -> float:
    dh = abs(h_ac_m - h_gs_m)
    return math.sqrt(ground_range_m**2 + dh**2)


def elevation_deg(ground_range_m: float, h_ac_m: float, h_gs_m: float = 0.0) -> float:
    dh = h_ac_m - h_gs_m
    return math.degrees(math.atan2(dh, max(ground_range_m, 1e-9)))


def fresnel_radius_m(d1_m: float, d2_m: float, freq_hz: float, n: int = 1) -> float:
    lam = C_MPS / freq_hz
    d = d1_m + d2_m
    if d <= 0.0:
        raise ValueError("d1+d2 must be > 0")
    return math.sqrt(n * lam * d1_m * d2_m / d)


def fresnel_clearance_ok(clearance_m: float, f1_m: float, fraction: float = 0.6) -> bool:
    return clearance_m >= fraction * f1_m


def two_ray_pl_db(distance_m: float, h_tx_m: float, h_rx_m: float, freq_hz: float) -> float:
    """Flat-Earth two-ray. Far-field ~ 40 log10(d) - 20 log10(h_t h_r)."""
    if min(distance_m, h_tx_m, h_rx_m, freq_hz) <= 0.0:
        raise ValueError("two-ray inputs must be > 0")
    lam = C_MPS / freq_hz
    d_los = math.sqrt(distance_m**2 + (h_tx_m - h_rx_m) ** 2)
    d_ref = math.sqrt(distance_m**2 + (h_tx_m + h_rx_m) ** 2)
    # Magnitude of (e^{-jkd1}/d1 + Γ e^{-jkd2}/d2) with Γ≈-1 (ground).
    k = 2.0 * math.pi / lam
    e1 = complex(math.cos(-k * d_los), math.sin(-k * d_los)) / d_los
    e2 = -complex(math.cos(-k * d_ref), math.sin(-k * d_ref)) / d_ref
    mag = abs(e1 + e2)
    if mag <= 0.0:
        mag = 1e-15
    # Free-space factor lambda/(4π)
    fs = lam / (4.0 * math.pi)
    return -20.0 * math.log10(fs * mag)


def aircraft_doppler_hz(x_m: float, h_m: float, v_mps: float, freq_hz: float) -> float:
    """Peak positive at approach (x<0), zero at overhead (x=0), negative at departure.

    Aircraft flies +x (increasing x). Radial unit is x/r, so v_radial = v * x/r.
    Sign is flipped so approach is positive: f_d = -(v/c)*f*(x/r).
    """
    r = math.sqrt(x_m**2 + h_m**2)
    if r <= 0.0:
        return 0.0
    return -(v_mps / C_MPS) * freq_hz * (x_m / r)


def a2g_snapshot(cfg: dict) -> dict:
    h_ac = float(cfg.get("aircraft_alt_m", 300.0))
    h_gs = float(cfg.get("gs_alt_m", 1.5))
    x_m = float(cfg.get("along_track_m", -2000.0))
    ground = abs(x_m)
    v = float(cfg.get("velocity_mps", 70.0))
    freq = float(cfg["freq_hz"])
    allow = bool(cfg.get("allow_beyond_horizon", False))
    horizon = radio_horizon_m(h_ac, h_gs)
    rng = slant_range_m(ground, h_ac, h_gs)
    if rng > horizon and not allow:
        raise HorizonError(
            f"A2G path {rng:.1f} m exceeds radio horizon {horizon:.1f} m "
            "(set allow_beyond_horizon to model anyway)"
        )
    pl_fs = fspl_db_from_m_hz(rng, freq)
    pl_2r = two_ray_pl_db(max(ground, 1.0), h_ac, h_gs, freq)
    d1 = rng * (h_gs / max(h_ac + h_gs, 1e-9))
    d2 = rng - d1
    f1 = fresnel_radius_m(max(d1, 1.0), max(d2, 1.0), freq)
    return {
        "source": SOURCE_MODELED,
        "disclaimer": MODELED_DISCLAIMER,
        "ground_range_m": ground,
        "slant_range_m": rng,
        "elevation_deg": elevation_deg(ground, h_ac, h_gs),
        "radio_horizon_m": horizon,
        "beyond_horizon": rng > horizon,
        "doppler_hz": aircraft_doppler_hz(x_m, h_ac - h_gs, v, freq),
        "fspl_db": pl_fs,
        "two_ray_pl_db": pl_2r,
        "fresnel_f1_m": f1,
        "t_prop_ms": 1000.0 * rng / C_MPS,
        "path_loss_db": pl_2r,
    }
