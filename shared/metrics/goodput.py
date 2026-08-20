"""Goodput, PDR/PLR, message rate, interface counters (read-only)."""

from __future__ import annotations

from dataclasses import dataclass, field


def goodput_bps(useful_bytes: int, elapsed_s: float) -> float:
    if elapsed_s <= 0.0:
        raise ValueError("elapsed_s must be > 0")
    return 8.0 * useful_bytes / elapsed_s


def message_rate_hz(count: int, elapsed_s: float) -> float:
    if elapsed_s <= 0.0:
        raise ValueError("elapsed_s must be > 0")
    return count / elapsed_s


@dataclass
class SequenceStats:
    """Gap / duplicate / reorder are counted separately from PLR."""

    expected: int | None = None
    received: int = 0
    duplicates: int = 0
    gaps: int = 0
    reorders: int = 0
    last_seq: int | None = None
    _seen: set[int] = field(default_factory=set)

    def observe(self, seq: int) -> None:
        self.received += 1
        if seq in self._seen:
            self.duplicates += 1
            return
        self._seen.add(seq)
        if self.expected is None:
            self.expected = seq
            self.last_seq = seq
            return
        if seq == self.last_seq:  # pragma: no cover - seen-set already handles
            self.duplicates += 1
            return
        if self.last_seq is not None and seq < self.last_seq:
            self.reorders += 1
            return
        if self.last_seq is not None and seq > self.last_seq + 1:
            self.gaps += seq - self.last_seq - 1
        self.last_seq = seq

    def pdr(self) -> float | None:
        if self.last_seq is None or self.expected is None:
            return None
        expected_count = self.last_seq - self.expected + 1
        if expected_count <= 0:
            return None
        unique = self.received - self.duplicates
        return unique / expected_count

    def plr(self) -> float | None:
        p = self.pdr()
        if p is None:
            return None
        return 1.0 - p


# Documented overhead stack (bytes), used only for modeled L1/L2 estimates.
OVERHEAD_STACK = {
    "ipv4_header": 20,
    "tcp_header": 20,
    "mqtt_publish_min": 2,
    "ethernet": 18,
    "nr_mac_pdcp_approx": 8,
    "note": "Application goodput excludes headers. Air-interface modeled rate uses NR MAC approx.",
}
