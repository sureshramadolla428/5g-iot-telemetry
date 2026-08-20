from __future__ import annotations

import random

from iot_schema.telemetry import (
    BATT_MAX,
    BATT_MIN,
    HUM_MAX,
    HUM_MIN,
    LAT_MAX,
    LAT_MIN,
    LON_MAX,
    LON_MIN,
    TEMP_MAX,
    TEMP_MIN,
    DeviceState,
    snapshot_payload,
    step_random_walk,
)


def test_random_walk_stays_in_bounds():
    rng = random.Random(42)
    state = DeviceState(device_id="iot-bounds")
    for _ in range(5000):
        step_random_walk(state, rng)
        assert TEMP_MIN <= state.temperature <= TEMP_MAX
        assert HUM_MIN <= state.humidity <= HUM_MAX
        assert BATT_MIN <= state.battery <= BATT_MAX
        assert LAT_MIN <= state.latitude <= LAT_MAX
        assert LON_MIN <= state.longitude <= LON_MAX


def test_battery_drains_monotonically_until_empty():
    rng = random.Random(7)
    state = DeviceState(device_id="iot-batt", battery=10.0)
    last = state.battery
    for _ in range(400):
        step_random_walk(state, rng)
        assert state.battery <= last + 1e-9
        last = state.battery
    assert state.battery == 0.0


def test_snapshot_payload_matches_state():
    state = DeviceState(device_id="iot-001", temperature=20.0, humidity=50.0, battery=90.0)
    payload = snapshot_payload(state)
    assert payload.device_id == "iot-001"
    assert payload.status in ("online", "offline", "degraded")
