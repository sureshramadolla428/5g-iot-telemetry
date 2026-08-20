"""Load per-device YAML mapping: device_id -> interface / source_ip."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from iot_schema.bind import BindError, require_explicit_source_ip


@dataclass(frozen=True)
class DeviceBind:
    device_id: str
    interface: str | None
    source_ip: str | None


MAX_DIRECT_FLEET = 100


def generate_direct_fleet(count: int) -> list[DeviceBind]:
    if count < 1:
        raise BindError("DEVICE_COUNT / count must be >= 1")
    if count > MAX_DIRECT_FLEET:
        raise BindError(
            f"DEVICE_COUNT={count} exceeds max {MAX_DIRECT_FLEET} on this shared lab host"
        )
    return [
        DeviceBind(device_id=f"iot-{i:03d}", interface=None, source_ip=None)
        for i in range(1, count + 1)
    ]


def load_device_map(
    path: str | Path,
    bind_mode: str,
    *,
    count: int | None = None,
) -> list[DeviceBind]:
    raw = Path(path).read_text(encoding="utf-8")
    data: dict[str, Any] = yaml.safe_load(raw) or {}
    yaml_count = data.get("count")
    if count is None and yaml_count is not None:
        count = int(yaml_count)
    rows = data.get("devices")
    mode = (bind_mode or "").strip().lower()
    if mode == "direct" and (not isinstance(rows, list) or not rows) and count:
        return generate_direct_fleet(count)
    if not isinstance(rows, list) or not rows:
        raise BindError(f"device map {path} has no devices list")
    devices: list[DeviceBind] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or "device_id" not in row:
            raise BindError(f"invalid device entry: {row!r}")
        device_id = str(row["device_id"])
        if device_id in seen:
            raise BindError(f"duplicate device_id {device_id}")
        seen.add(device_id)
        interface = row.get("interface")
        source_ip = row.get("source_ip")
        if isinstance(interface, str):
            interface = interface.strip() or None
        else:
            interface = None
        if source_ip is not None:
            source_ip = str(source_ip)
        resolved = require_explicit_source_ip(
            source_ip, bind_mode=bind_mode, device_id=device_id, interface=interface
        )
        devices.append(DeviceBind(device_id=device_id, interface=interface, source_ip=resolved))
    if count is not None and count > len(devices):
        if mode == "5g":
            raise BindError(
                f"BIND_MODE=5g cannot invent UEs: map has {len(devices)} explicit "
                f"source_ip entries, DEVICE_COUNT={count}. Each 5G device needs its own "
                f"uesimtun IP. Use BIND_MODE=direct to simulate a {count}-UE fleet "
                f"without extra tunnels (does not use the 5G user plane)."
            )
        extra = generate_direct_fleet(count)[len(devices) :]
        devices.extend(extra)
    if count is not None:
        devices = devices[:count]
    return devices
