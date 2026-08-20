"""NTN geometry and link metrics (modeled). Does not modify any NTN lab project."""

from __future__ import annotations

import math

from metrics.constants import C_MPS, GEO_ALTITUDE_KM, K_BOLTZMANN, R_E_M
from metrics.convert import lin_power_to_db
from metrics.pathloss import fspl_db_from_m_hz


def slant_range_m(altitude_m: float, elevation_deg: float) -> float:
    """Slant range from Earth terminal at elevation ε to spherical-orbit satellite."""
    if altitude_m <= 0.0:
        raise ValueError("altitude must be > 0")
    eps = math.radians(elevation_deg)
    # d = R_e * (sqrt(((Re+h)/Re)^2 - cos^2 ε) - sin ε)
    inner = ((R_E_M + altitude_m) / R_E_M) ** 2 - math.cos(eps) ** 2
    if inner <= 0.0:
        raise ValueError("elevation/geometry invalid for slant range")
    return R_E_M * (math.sqrt(inner) - math.sin(eps))


def one_way_delay_s(distance_m: float) -> float:
    return distance_m / C_MPS


def geo_nadir_one_way_s() -> float:
    return (GEO_ALTITUDE_KM * 1000.0) / C_MPS


def circular_orbit_speed_mps(altitude_m: float) -> float:
    """v = sqrt(μ / (R_e+h)), μ = 3.986004418e14 m^3/s^2."""
    mu = 3.986004418e14
    return math.sqrt(mu / (R_E_M + altitude_m))


def ntn_doppler_hz(altitude_m: float, freq_hz: float, elevation_deg: float) -> float:
    """Approximate radial Doppler using orbit speed and elevation (modeled)."""
    v = circular_orbit_speed_mps(altitude_m)
    # Radial component falls toward 0 at zenith.
    return (v / C_MPS) * freq_hz * math.cos(math.radians(elevation_deg))


def gt_dbk(g_rx_dbi: float, t_sys_k: float) -> float:
    if t_sys_k <= 0.0:
        raise ValueError("T_sys must be > 0")
    return g_rx_dbi - 10.0 * math.log10(t_sys_k)


def cn0_dbhz(
    eirp_dbw: float,
    path_loss_db: float,
    gt: float,
    extra_loss_db: float = 0.0,
) -> float:
    """C/N0 = EIRP - PL - L + G/T - 10 log10(k). k in dBW/K/Hz."""
    k_dbw = 10.0 * math.log10(K_BOLTZMANN)
    return eirp_dbw - path_loss_db - extra_loss_db + gt - k_dbw


def ntn_snapshot(cfg: dict) -> dict:
    alt_m = float(cfg.get("altitude_km", GEO_ALTITUDE_KM)) * 1000.0
    elev = float(cfg.get("elevation_deg", 90.0))
    freq_hz = float(cfg["freq_hz"])
    rng = slant_range_m(alt_m, elev)
    rain = float(cfg.get("rain_loss_db", 0.0))
    gas = float(cfg.get("gas_loss_db", 0.0))
    scint = float(cfg.get("scintillation_db", 0.0))
    extra = rain + gas + scint
    pl = fspl_db_from_m_hz(rng, freq_hz) + extra
    eirp_dbw = float(cfg.get("eirp_dbw", 50.0))
    gt = gt_dbk(float(cfg.get("g_rx_dbi", 35.0)), float(cfg.get("t_sys_k", 150.0)))
    cn0 = cn0_dbhz(eirp_dbw, pl, gt)
    req = float(cfg.get("cn0_required_dbhz", 50.0))
    delay = one_way_delay_s(rng)
    return {
        "source": "modeled",
        "disclaimer": "modeled — not radio-measured",
        "orbit": cfg.get("orbit", "GEO"),
        "altitude_m": alt_m,
        "elevation_deg": elev,
        "slant_range_m": rng,
        "t_prop_one_way_ms": delay * 1000.0,
        "t_prop_rtt_ms": delay * 2000.0,
        "doppler_hz": ntn_doppler_hz(alt_m, freq_hz, elev),
        "fspl_plus_atm_db": pl,
        "g_t_dbk": gt,
        "cn0_dbhz": cn0,
        "cn0_margin_db": cn0 - req,
        "rain_loss_db": rain,
        "gas_loss_db": gas,
        "scintillation_db": scint,
        "path_loss_db": pl,
    }


def lin_snr_from_cn0(cn0_dbhz: float, bandwidth_hz: float) -> float:
    return lin_power_to_db(10.0 ** (cn0_dbhz / 10.0) / bandwidth_hz)
