"""Noise floor, SNR, SINR, Eb/N0, noise rise. Modeled unless tagged measured."""

from __future__ import annotations

import math

from metrics.constants import N0_DBM_PER_HZ
from metrics.convert import db_to_lin_power, lin_power_to_db


def noise_power_dbm(bandwidth_hz: float, noise_figure_db: float = 0.0) -> float:
    if bandwidth_hz <= 0.0:
        raise ValueError("bandwidth_hz must be > 0")
    return N0_DBM_PER_HZ + 10.0 * math.log10(bandwidth_hz) + noise_figure_db


def snr_db(p_rx_dbm: float, p_noise_dbm: float) -> float:
    return p_rx_dbm - p_noise_dbm


def sinr_db(signal_mw: float, interference_mw: float, noise_mw: float) -> float:
    den = interference_mw + noise_mw
    if den <= 0.0:
        raise ValueError("I+N must be > 0")
    if signal_mw <= 0.0:
        raise ValueError("signal power must be > 0")
    return lin_power_to_db(signal_mw / den)


def eb_n0_db(snr_db_value: float, bandwidth_hz: float, bit_rate_bps: float) -> float:
    """Eb/N0 = SNR * (B / R) → dB: SNR_dB + 10 log10(B/R)."""
    if bit_rate_bps <= 0.0 or bandwidth_hz <= 0.0:
        raise ValueError("bandwidth and bit rate must be > 0")
    return snr_db_value + 10.0 * math.log10(bandwidth_hz / bit_rate_bps)


def noise_rise_db(interference_mw: float, noise_mw: float) -> float:
    """(I+N)/N in dB."""
    if noise_mw <= 0.0:
        raise ValueError("noise_mw must be > 0")
    return lin_power_to_db((interference_mw + noise_mw) / noise_mw)


def thermal_noise_mw(bandwidth_hz: float, noise_figure_db: float = 0.0) -> float:
    return db_to_lin_power(noise_power_dbm(bandwidth_hz, noise_figure_db))
