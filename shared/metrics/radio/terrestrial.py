"""Default terrestrial TR 38.901 UMa-ish modeled radio."""

from __future__ import annotations

from typing import Any

from metrics.constants import MODELED_DISCLAIMER, SOURCE_MODELED
from metrics.convert import dbm_to_mw
from metrics.harq import reliability, residual_bler
from metrics.link_budget import eirp_dbm, p_rx_dbm
from metrics.mobility import (
    coherence_bandwidth_hz,
    coherence_time_s,
    doppler_hz,
    scs_doppler_warning,
)
from metrics.noise import noise_power_dbm, sinr_db, snr_db, thermal_noise_mw
from metrics.pathloss import uma_los_pl_db
from metrics.phy import (
    cqi_from_sinr_approx,
    lookup_cqi,
    lookup_mcs,
    mcs_for_cqi,
    transport_block_size,
)
from metrics.radio.base import assert_modeled_rf
from metrics.ts38215 import modeled_rsrp_bundle


class TerrestrialUmaModel:
    name = "terrestrial_uma"

    def snapshot(self, cfg: dict[str, Any]) -> dict[str, Any]:
        freq_hz = float(cfg["freq_hz"])
        freq_ghz = freq_hz / 1e9
        d_2d = float(cfg.get("distance_2d_m", 200.0))
        h_bs = float(cfg.get("h_bs_m", 25.0))
        h_ut = float(cfg.get("h_ut_m", 1.5))
        bw = float(cfg.get("bandwidth_hz", 20e6))
        nf = float(cfg.get("noise_figure_db", 7.0))
        n_prb = int(cfg.get("n_prb", 51))
        layers = int(cfg.get("layers", 1))
        n_re = int(cfg.get("n_re", n_prb * 12 * 11))
        cqi_table = int(cfg.get("cqi_table", 1))
        bler = float(cfg.get("bler_target", 0.1))
        harq_tx = int(cfg.get("max_harq_tx", 4))
        v = float(cfg.get("velocity_mps", 3.0))
        scs_hz = float(cfg.get("scs_khz", 30.0)) * 1e3
        delay_spread = float(cfg.get("delay_spread_s", 1e-6))
        i_over_n_db = float(cfg.get("interference_over_noise_db", 0.0))

        pl, segment, d_bp = uma_los_pl_db(d_2d, h_bs, h_ut, freq_ghz)
        eirp = eirp_dbm(
            float(cfg.get("p_tx_dbm", 23.0)),
            float(cfg.get("g_tx_dbi", 8.0)),
            float(cfg.get("l_feeder_db", 0.0)),
        )
        prx = p_rx_dbm(
            eirp,
            pl,
            float(cfg.get("g_rx_dbi", 0.0)),
            float(cfg.get("l_rx_db", 0.0)),
        )
        p_n = noise_power_dbm(bw, nf)
        snr = snr_db(prx, p_n)
        n_mw = thermal_noise_mw(bw, nf)
        i_mw = n_mw * (10.0 ** (i_over_n_db / 10.0))
        s_mw = dbm_to_mw(prx)
        sinr = sinr_db(s_mw, i_mw, n_mw)
        radio = modeled_rsrp_bundle(p_rx_dbm=prx, n_prb=n_prb, sinr_db_value=sinr)
        cqi = cqi_from_sinr_approx(sinr, cqi_table)
        cqi_row = lookup_cqi(cqi_table, cqi) if cqi else None
        mcs = mcs_for_cqi(cqi_row) if cqi_row else 0
        mcs_row = lookup_mcs(mcs)
        tbs = transport_block_size(
            n_re, mcs_row["code_rate_x1024"] / 1024.0, mcs_row["qm"], layers
        )
        fd = doppler_hz(v, freq_hz, 0.0)
        out = {
            **radio,
            "model": self.name,
            "path_loss_db": pl,
            "uma_segment": segment,
            "d_bp_prime_m": d_bp,
            "eirp_dbm": eirp,
            "p_rx_dbm": prx,
            "snr_db": snr,
            "sinr_db": sinr,
            "cqi": cqi,
            "cqi_table": cqi_table,
            "mcs": mcs,
            "tbs_bits": tbs,
            "bler_target": bler,
            "residual_bler": residual_bler(bler, harq_tx),
            "reliability": reliability(bler, harq_tx),
            "doppler_hz": fd,
            "coherence_time_s": coherence_time_s(max(abs(fd), 0.1)),
            "coherence_bw_hz": coherence_bandwidth_hz(delay_spread),
            "scs_doppler_warning": scs_doppler_warning(fd, scs_hz),
            "source": SOURCE_MODELED,
            "disclaimer": MODELED_DISCLAIMER,
        }
        assert_modeled_rf(out)
        return out
