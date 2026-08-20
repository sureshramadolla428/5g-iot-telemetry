"""Explicit source-IP binding for 5G user-plane MQTT sockets.

Never auto-select the first uesimtunN interface. BIND_MODE=5g fails if source_ip
is missing, empty, or the sentinel 'auto'.
"""

from __future__ import annotations

import socket
from typing import Any

AUTO_SENTINELS = {"", "auto", "auto-select", "first", "any"}


class BindError(RuntimeError):
    """Raised when 5G bind configuration is unsafe or incomplete."""


def require_explicit_source_ip(
    source_ip: str | None,
    *,
    bind_mode: str,
    device_id: str,
    interface: str | None = None,
) -> str | None:
    """Validate bind policy. Returns the IP to bind, or None in direct mode."""
    mode = (bind_mode or "").strip().lower()
    if mode == "direct":
        return None
    if mode != "5g":
        raise BindError(
            f"device {device_id}: BIND_MODE must be '5g' or 'direct', got {bind_mode!r}"
        )
    if source_ip is None or source_ip.strip().lower() in AUTO_SENTINELS:
        raise BindError(
            f"device {device_id}: BIND_MODE=5g requires an explicit source_ip "
            f"(interface={interface!r}). Refusing to auto-select uesimtunN."
        )
    ip = source_ip.strip()
    try:
        socket.inet_pton(socket.AF_INET, ip)
    except OSError as exc:
        raise BindError(f"device {device_id}: invalid IPv4 source_ip {ip!r}") from exc
    if ip.endswith(".0") or ip.endswith(".255"):
        raise BindError(
            f"device {device_id}: source_ip {ip} looks like a network/broadcast address"
        )
    return ip


def create_source_bound_socket(
    source_ip: str | None,
    *,
    bind_mode: str,
    device_id: str,
    interface: str | None = None,
    sock_cls: Any = socket.socket,
) -> socket.socket:
    """Create a TCP socket. In 5g mode, bind((source_ip, 0)) before connect."""
    bind_ip = require_explicit_source_ip(
        source_ip, bind_mode=bind_mode, device_id=device_id, interface=interface
    )
    sock = sock_cls(socket.AF_INET, socket.SOCK_STREAM)
    if bind_ip is not None:
        try:
            sock.bind((bind_ip, 0))
        except OSError as exc:
            sock.close()
            raise BindError(
                f"device {device_id}: failed to bind source {bind_ip} "
                f"(interface={interface!r}): {exc}"
            ) from exc
    return sock
