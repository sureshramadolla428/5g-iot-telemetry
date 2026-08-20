"""Read-only host interface counters from /proc/net/dev or `ip -s link`."""

from __future__ import annotations

import subprocess
from pathlib import Path


def parse_proc_net_dev(text: str, ifname: str) -> dict[str, int] | None:
    for line in text.splitlines():
        if ":" not in line:
            continue
        name, rest = line.split(":", 1)
        if name.strip() != ifname:
            continue
        parts = rest.split()
        if len(parts) < 16:
            return None
        return {
            "rx_bytes": int(parts[0]),
            "rx_packets": int(parts[1]),
            "rx_errs": int(parts[2]),
            "rx_drop": int(parts[3]),
            "tx_bytes": int(parts[8]),
            "tx_packets": int(parts[9]),
            "tx_errs": int(parts[10]),
            "tx_drop": int(parts[11]),
        }
    return None


def read_interface_counters(ifname: str) -> dict[str, int] | None:
    """Read-only. Never creates or modifies interfaces."""
    proc = Path("/proc/net/dev")
    if proc.is_file():
        parsed = parse_proc_net_dev(proc.read_text(encoding="utf-8"), ifname)
        if parsed is not None:
            return parsed
    try:
        out = subprocess.run(
            ["ip", "-s", "link", "show", "dev", ifname],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None
    if out.returncode != 0:
        return None
    return _parse_ip_s_link(out.stdout)


def _parse_ip_s_link(text: str) -> dict[str, int] | None:
    rx_b = tx_b = rx_p = tx_p = None
    lines = [ln.strip() for ln in text.splitlines()]
    for i, ln in enumerate(lines):
        if ln.startswith("RX:") and i + 1 < len(lines):
            cols = lines[i + 1].split()
            if cols:
                rx_b, rx_p = int(cols[0]), int(cols[1])
        if ln.startswith("TX:") and i + 1 < len(lines):
            cols = lines[i + 1].split()
            if cols:
                tx_b, tx_p = int(cols[0]), int(cols[1])
    if None in (rx_b, tx_b, rx_p, tx_p):
        return None
    return {
        "rx_bytes": rx_b or 0,
        "rx_packets": rx_p or 0,
        "rx_errs": 0,
        "rx_drop": 0,
        "tx_bytes": tx_b or 0,
        "tx_packets": tx_p or 0,
        "tx_errs": 0,
        "tx_drop": 0,
    }


def throughput_bps(bytes_a: int, bytes_b: int, elapsed_s: float) -> float:
    if elapsed_s <= 0.0:
        raise ValueError("elapsed_s must be > 0")
    return 8.0 * max(bytes_b - bytes_a, 0) / elapsed_s
