from __future__ import annotations

from pathlib import Path

import pytest

from iot_schema.bind import BindError
from iot_schema.device_map import load_device_map


def test_load_map_5g_rejects_placeholder(tmp_path: Path):
    path = tmp_path / "devices.yaml"
    path.write_text(
        "devices:\n  - device_id: iot-001\n    interface: uesimtun0\n    source_ip: auto\n",
        encoding="utf-8",
    )
    with pytest.raises(BindError):
        load_device_map(path, "5g")


def test_load_map_direct_allows_missing_ip(tmp_path: Path):
    path = tmp_path / "devices.yaml"
    path.write_text(
        "devices:\n  - device_id: iot-001\n    interface: uesimtun0\n",
        encoding="utf-8",
    )
    devices = load_device_map(path, "direct")
    assert devices[0].device_id == "iot-001"
def test_direct_fleet_count(tmp_path: Path):
    path = tmp_path / "devices.yaml"
    path.write_text("count: 5\ndevices: []\n", encoding="utf-8")
    devices = load_device_map(path, "direct", count=5)
    assert [d.device_id for d in devices] == [f"iot-{i:03d}" for i in range(1, 6)]


def test_5g_refuses_to_invent_ues(tmp_path: Path):
    path = tmp_path / "devices.yaml"
    path.write_text(
        "devices:\n  - device_id: iot-001\n    source_ip: 10.45.0.2\n",
        encoding="utf-8",
    )
    with pytest.raises(BindError, match="cannot invent"):
        load_device_map(path, "5g", count=50)
