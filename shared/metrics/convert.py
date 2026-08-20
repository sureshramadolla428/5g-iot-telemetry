"""dB / linear conversions. Average RF power in the linear domain only."""

from __future__ import annotations

import math
from collections.abc import Iterable


def dbm_to_mw(dbm: float) -> float:
    return 10.0 ** (dbm / 10.0)


def mw_to_dbm(mw: float) -> float:
    if mw <= 0.0:
        raise ValueError("power in mW must be > 0")
    return 10.0 * math.log10(mw)


def db_to_lin_power(db: float) -> float:
    """Power ratio: 10^(dB/10)."""
    return 10.0 ** (db / 10.0)


def lin_power_to_db(lin: float) -> float:
    if lin <= 0.0:
        raise ValueError("linear power ratio must be > 0")
    return 10.0 * math.log10(lin)


def db_to_lin_amplitude(db: float) -> float:
    """Amplitude / field ratio: 10^(dB/20)."""
    return 10.0 ** (db / 20.0)


def lin_amplitude_to_db(lin: float) -> float:
    if lin <= 0.0:
        raise ValueError("linear amplitude ratio must be > 0")
    return 20.0 * math.log10(lin)


def avg_db(values_db: Iterable[float], *, kind: str = "power") -> float:
    """Average quantities given in dB by converting to linear first.

    kind='power' uses 10^(x/10) (RSRP, RSSI, SNR).
    kind='amplitude' uses 10^(x/20).
    NEVER average dB values arithmetically.
    """
    vals = list(values_db)
    if not vals:
        raise ValueError("avg_db requires at least one sample")
    if kind == "power":
        lin = [db_to_lin_power(v) for v in vals]
        return lin_power_to_db(sum(lin) / len(lin))
    if kind == "amplitude":
        lin = [db_to_lin_amplitude(v) for v in vals]
        return lin_amplitude_to_db(sum(lin) / len(lin))
    raise ValueError("kind must be 'power' or 'amplitude'")
