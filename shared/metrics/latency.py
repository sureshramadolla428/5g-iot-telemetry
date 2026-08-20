"""Latency: measured RTT/OWD/jitter/PDV and modeled user-plane breakdown."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from metrics.constants import C_MPS


@dataclass
class Rfc3550Jitter:
    """RFC 3550 interarrival jitter (same units as timestamps, typically ms)."""

    jitter: float = 0.0
    prev_transit: float | None = None

    def update(self, send_ts: float, recv_ts: float) -> float:
        transit = recv_ts - send_ts
        if self.prev_transit is None:
            self.prev_transit = transit
            return self.jitter
        delta = abs(transit - self.prev_transit)
        self.prev_transit = transit
        self.jitter += (delta - self.jitter) / 16.0
        return self.jitter


def one_way_delay_ms(rtt_ms: float, clocks_synced: bool) -> float | None:
    """OWD is RTT/2 only when clocks are known synced; else null."""
    if not clocks_synced:
        return None
    return rtt_ms / 2.0


def percentile(sorted_samples: list[float], p: float) -> float:
    if not sorted_samples:
        raise ValueError("no samples")
    if not 0.0 <= p <= 100.0:
        raise ValueError("percentile out of range")
    k = (len(sorted_samples) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_samples[int(k)]
    return sorted_samples[f] * (c - k) + sorted_samples[c] * (k - f)


def rfc3393_pdv_ms(delays_ms: list[float]) -> dict[str, float]:
    """RFC 3393 PDV relative to minimum delay in the window."""
    if len(delays_ms) < 2:
        raise ValueError("PDV needs at least two delay samples")
    dmin = min(delays_ms)
    pdv = sorted(d - dmin for d in delays_ms)
    return {
        "pdv_p50_ms": percentile(pdv, 50),
        "pdv_p95_ms": percentile(pdv, 95),
        "pdv_p99_ms": percentile(pdv, 99),
        "pdv_min_ms": pdv[0],
        "pdv_max_ms": pdv[-1],
    }


def t_prop_ms(distance_m: float) -> float:
    return 1000.0 * distance_m / C_MPS


def modeled_up_latency_ms(
    *,
    t_proc_ms: float,
    t_queue_ms: float,
    t_tx_ms: float,
    distance_m: float,
    t_harq_ms: float = 0.0,
    extra_ms: float = 0.0,
) -> dict[str, float]:
    prop = t_prop_ms(distance_m)
    total = t_proc_ms + t_queue_ms + t_tx_ms + prop + t_harq_ms + extra_ms
    return {
        "t_proc_ms": t_proc_ms,
        "t_queue_ms": t_queue_ms,
        "t_tx_ms": t_tx_ms,
        "t_prop_ms": prop,
        "t_harq_ms": t_harq_ms,
        "t_extra_ms": extra_ms,
        "l_up_ms": total,
    }


def latency_budget_pct(latency_ms: float, budget_ms: float) -> float:
    if budget_ms <= 0.0:
        raise ValueError("budget_ms must be > 0")
    return 100.0 * latency_ms / budget_ms


@dataclass
class DelayWindow:
    samples_ms: list[float] = field(default_factory=list)
    max_size: int = 256

    def add(self, delay_ms: float) -> None:
        self.samples_ms.append(delay_ms)
        if len(self.samples_ms) > self.max_size:
            self.samples_ms = self.samples_ms[-self.max_size :]

    def pdv(self) -> dict[str, float] | None:
        if len(self.samples_ms) < 2:
            return None
        return rfc3393_pdv_ms(self.samples_ms)
