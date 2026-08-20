"""HARQ / BLER / PER / residual reliability (modeled)."""

from __future__ import annotations


def residual_bler(bler: float, max_harq_tx: int) -> float:
    """Independent HARQ attempts: BLER^N_tx."""
    if not (0.0 <= bler <= 1.0) or max_harq_tx < 1:
        raise ValueError("invalid BLER or HARQ count")
    return bler**max_harq_tx


def packet_error_rate(bler: float, tbs_per_packet: int = 1) -> float:
    """PER = 1 - (1-BLER)^N_TB for N transport blocks per packet."""
    if tbs_per_packet < 1:
        raise ValueError("tbs_per_packet must be >= 1")
    return 1.0 - (1.0 - bler) ** tbs_per_packet


def reliability(bler: float, max_harq_tx: int, packets: int = 1) -> float:
    """Probability all packets succeed after HARQ."""
    p_ok = 1.0 - residual_bler(bler, max_harq_tx)
    return p_ok**packets
