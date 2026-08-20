"""TS 38.215 SS-RSRP / RSSI / RSRQ / SS-SINR and 38.133-style report mapping.

All outputs from this module are MODELED unless a future SDR radio model
implements RadioModel with source='measured'. UERANSIM has no PHY.
"""

from __future__ import annotations

import math

from metrics.constants import MODELED_DISCLAIMER, SOURCE_MODELED
from metrics.convert import dbm_to_mw, mw_to_dbm

# TS 38.133 reporting ranges (SS-RSRP / SS-RSRQ / SS-SINR).
SS_RSRP_DBM_MIN, SS_RSRP_DBM_MAX = -156.0, -31.0
SS_RSRQ_DB_MIN, SS_RSRQ_DB_MAX = -43.0, 20.0
SS_SINR_DB_MIN, SS_SINR_DB_MAX = -23.0, 40.0


def rsrq_linear(rsrp_mw: float, rssi_mw: float, n_prb: int) -> float:
    """RSRQ = N * RSRP / RSSI (linear power). TS 38.215."""
    if rssi_mw <= 0.0 or n_prb <= 0:
        raise ValueError("RSSI and N_PRB must be > 0")
    return n_prb * rsrp_mw / rssi_mw


def rsrq_db(rsrp_dbm: float, rssi_dbm: float, n_prb: int) -> float:
    """Identity: RSRQ_dB = RSRP_dBm - RSSI_dBm + 10 log10(N)."""
    return rsrp_dbm - rssi_dbm + 10.0 * math.log10(n_prb)


def ss_sinr_db(sss_re_mw: float, interference_plus_noise_mw: float) -> float:
    if interference_plus_noise_mw <= 0.0 or sss_re_mw <= 0.0:
        raise ValueError("SS-SINR requires positive S and I+N")
    return 10.0 * math.log10(sss_re_mw / interference_plus_noise_mw)


def quantize_ss_rsrp(rsrp_dbm: float) -> int:
    """Map dBm to TS 38.133 SS-RSRP report 0..127 (1 dB steps, offset 156)."""
    if rsrp_dbm < SS_RSRP_DBM_MIN:
        return 0
    if rsrp_dbm >= SS_RSRP_DBM_MAX:
        return 127
    return int(round(rsrp_dbm - SS_RSRP_DBM_MIN)) + 1


def dequantize_ss_rsrp(report: int) -> float:
    report = max(0, min(127, report))
    return SS_RSRP_DBM_MIN + max(report - 1, 0)


def quantize_ss_rsrq(rsrq_db: float) -> int:
    """0.5 dB steps, offset 43 (report 0..127)."""
    if rsrq_db < SS_RSRQ_DB_MIN:
        return 0
    if rsrq_db >= SS_RSRQ_DB_MAX:
        return 127
    return int(round((rsrq_db - SS_RSRQ_DB_MIN) / 0.5)) + 1


def quantize_ss_sinr(sinr_db: float) -> int:
    """0.5 dB steps, offset 23."""
    if sinr_db < SS_SINR_DB_MIN:
        return 0
    if sinr_db >= SS_SINR_DB_MAX:
        return 127
    return int(round((sinr_db - SS_SINR_DB_MIN) / 0.5)) + 1


def modeled_rsrp_bundle(
    *,
    p_rx_dbm: float,
    n_prb: int,
    rssi_overhead_db: float = 3.0,
    sinr_db_value: float,
) -> dict[str, float | int | str]:
    """Build tagged modeled radio from wideband P_rx.

    SS-RSRP is per-RE: P_rx minus 10 log10(12 * N_PRB). Wideband P_rx must not
    be plotted as RSRP (that made RSRP look ~30 dB too strong vs SINR).
    """
    n_re_meas = max(1, 12 * int(n_prb))
    rsrp_dbm = p_rx_dbm - 10.0 * math.log10(n_re_meas)
    rsrp_dbm = max(SS_RSRP_DBM_MIN, min(SS_RSRP_DBM_MAX, rsrp_dbm))
    rsrp_mw = dbm_to_mw(rsrp_dbm)
    rssi_dbm = rsrp_dbm + rssi_overhead_db + 10.0 * math.log10(n_prb)
    rssi_mw = dbm_to_mw(rssi_dbm)
    rsrq = rsrq_db(rsrp_dbm, rssi_dbm, n_prb)
    return {
        "source": SOURCE_MODELED,
        "disclaimer": MODELED_DISCLAIMER,
        "rsrp_dbm": rsrp_dbm,
        "rsrp_mw": rsrp_mw,
        "rssi_dbm": rssi_dbm,
        "rssi_mw": rssi_mw,
        "rsrq_db": rsrq,
        "ss_sinr_db": sinr_db_value,
        "ss_rsrp_report": quantize_ss_rsrp(rsrp_dbm),
        "ss_rsrq_report": quantize_ss_rsrq(rsrq),
        "ss_sinr_report": quantize_ss_sinr(sinr_db_value),
        "n_prb": n_prb,
        "rsrp_check_dbm": mw_to_dbm(rsrp_mw),
    }
