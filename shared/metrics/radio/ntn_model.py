"""NTN RadioModel wrapper."""

from __future__ import annotations

from typing import Any

from metrics.constants import MODELED_DISCLAIMER, SOURCE_MODELED
from metrics.convert import dbm_to_mw
from metrics.link_budget import eirp_dbm, p_rx_dbm
from metrics.noise import noise_power_dbm, snr_db
from metrics.ntn import ntn_snapshot
from metrics.phy import cqi_from_sinr_approx
from metrics.radio.base import assert_modeled_rf
from metrics.ts38215 import modeled_rsrp_bundle


class NtnRadioModel:
    name = "ntn"

    def snapshot(self, cfg: dict[str, Any]) -> dict[str, Any]:
        ntn = ntn_snapshot(cfg)
        bw = float(cfg.get("bandwidth_hz", 10e6))
        nf = float(cfg.get("noise_figure_db", 2.0))
        n_prb = int(cfg.get("n_prb", 24))
        eirp = eirp_dbm(float(cfg.get("p_tx_dbm", 30.0)), float(cfg.get("g_tx_dbi", 20.0)))
        prx = p_rx_dbm(eirp, ntn["path_loss_db"], float(cfg.get("g_rx_dbi", 35.0)))
        snr = snr_db(prx, noise_power_dbm(bw, nf))
        radio = modeled_rsrp_bundle(p_rx_dbm=prx, n_prb=n_prb, sinr_db_value=snr)
        cqi = cqi_from_sinr_approx(snr, int(cfg.get("cqi_table", 1)))
        out = {
            **radio,
            **ntn,
            "model": self.name,
            "eirp_dbm": eirp,
            "p_rx_dbm": prx,
            "snr_db": snr,
            "sinr_db": snr,
            "cqi": cqi,
            "rsrp_mw": dbm_to_mw(radio["rsrp_dbm"]),  # type: ignore[arg-type]
            "source": SOURCE_MODELED,
            "disclaimer": MODELED_DISCLAIMER,
        }
        assert_modeled_rf(out)
        return out
