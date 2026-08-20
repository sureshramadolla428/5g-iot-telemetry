"""A2G RadioModel wrapper."""

from __future__ import annotations

from typing import Any

from metrics.a2g import a2g_snapshot
from metrics.constants import MODELED_DISCLAIMER, SOURCE_MODELED
from metrics.link_budget import eirp_dbm, p_rx_dbm
from metrics.noise import noise_power_dbm, snr_db
from metrics.phy import cqi_from_sinr_approx
from metrics.radio.base import assert_modeled_rf
from metrics.ts38215 import modeled_rsrp_bundle


class A2gRadioModel:
    name = "a2g"

    def snapshot(self, cfg: dict[str, Any]) -> dict[str, Any]:
        a2g = a2g_snapshot(cfg)
        bw = float(cfg.get("bandwidth_hz", 20e6))
        nf = float(cfg.get("noise_figure_db", 7.0))
        n_prb = int(cfg.get("n_prb", 51))
        eirp = eirp_dbm(float(cfg.get("p_tx_dbm", 33.0)), float(cfg.get("g_tx_dbi", 6.0)))
        prx = p_rx_dbm(eirp, a2g["path_loss_db"], float(cfg.get("g_rx_dbi", 6.0)))
        snr = snr_db(prx, noise_power_dbm(bw, nf))
        radio = modeled_rsrp_bundle(p_rx_dbm=prx, n_prb=n_prb, sinr_db_value=snr)
        out = {
            **radio,
            **a2g,
            "model": self.name,
            "eirp_dbm": eirp,
            "p_rx_dbm": prx,
            "snr_db": snr,
            "sinr_db": snr,
            "cqi": cqi_from_sinr_approx(snr, int(cfg.get("cqi_table", 1))),
            "source": SOURCE_MODELED,
            "disclaimer": MODELED_DISCLAIMER,
        }
        assert_modeled_rf(out)
        return out
