"""Shared KPI formulas. Import from simulator, consumer, and tests — do not copy."""

from metrics.constants import (
    C_MPS,
    GEO_ALTITUDE_KM,
    K_BOLTZMANN,
    K_FACTOR,
    MODELED_DISCLAIMER,
    N0_DBM_PER_HZ,
    R_E_KM,
    SCHEMA_VERSION,
    SOURCE_MEASURED,
    SOURCE_MODELED,
    T0_K,
)
from metrics.convert import avg_db, db_to_lin_power, dbm_to_mw, mw_to_dbm
from metrics.radio.factory import build_radio_model, load_radio_config

__all__ = [
    "C_MPS",
    "GEO_ALTITUDE_KM",
    "K_BOLTZMANN",
    "K_FACTOR",
    "MODELED_DISCLAIMER",
    "N0_DBM_PER_HZ",
    "R_E_KM",
    "SCHEMA_VERSION",
    "SOURCE_MEASURED",
    "SOURCE_MODELED",
    "T0_K",
    "avg_db",
    "build_radio_model",
    "db_to_lin_power",
    "dbm_to_mw",
    "load_radio_config",
    "mw_to_dbm",
]
