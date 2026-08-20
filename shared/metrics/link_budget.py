"""Link budget: EIRP and received power."""

from __future__ import annotations


def eirp_dbm(p_tx_dbm: float, g_tx_dbi: float, l_feeder_db: float = 0.0) -> float:
    return p_tx_dbm + g_tx_dbi - l_feeder_db


def p_rx_dbm(
    eirp: float,
    path_loss_db: float,
    g_rx_dbi: float = 0.0,
    l_rx_db: float = 0.0,
    extra_loss_db: float = 0.0,
) -> float:
    return eirp - path_loss_db + g_rx_dbi - l_rx_db - extra_loss_db
