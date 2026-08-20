"""Random-walk telemetry generation with documented bounds."""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import UTC, datetime

from iot_schema.payload import MeasuredKpis, RadioKpis, TelemetryPayload
from metrics.constants import SCHEMA_VERSION

# Payload-format demo origin (Hyderabad). Not San Francisco — that made the
# world geomap look like Pacific / Australia wrap of one Bay-Area point.
GPS_ORIGIN_LAT = 17.1234
GPS_ORIGIN_LON = 78.1234

TEMP_MIN, TEMP_MAX = -40.0, 85.0
HUM_MIN, HUM_MAX = 0.0, 100.0
BATT_MIN, BATT_MAX = 0.0, 100.0
LAT_MIN, LAT_MAX = -90.0, 90.0
LON_MIN, LON_MAX = -180.0, 180.0


def _clip(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


@dataclass
class DeviceState:
    device_id: str
    temperature: float = 22.0
    humidity: float = 48.0
    battery: float = 100.0
    latitude: float = GPS_ORIGIN_LAT
    longitude: float = GPS_ORIGIN_LON
    status: str = "online"
    source_ip: str | None = None
    sequence_number: int = 0
    prev_lat: float | None = None
    prev_lon: float | None = None
    prev_ts: float | None = None


def step_random_walk(state: DeviceState, rng: random.Random) -> DeviceState:
    """Advance one sample: temperature/humidity walk, draining battery, drifting GPS."""
    state.temperature = _clip(state.temperature + rng.uniform(-0.35, 0.35), TEMP_MIN, TEMP_MAX)
    state.humidity = _clip(state.humidity + rng.uniform(-0.6, 0.6), HUM_MIN, HUM_MAX)
    drain = rng.uniform(0.01, 0.08)
    state.battery = _clip(state.battery - drain, BATT_MIN, BATT_MAX)
    old_lat, old_lon = state.latitude, state.longitude
    state.latitude = _clip(state.latitude + rng.uniform(-0.00012, 0.00012), LAT_MIN, LAT_MAX)
    state.longitude = _clip(state.longitude + rng.uniform(-0.00012, 0.00012), LON_MIN, LON_MAX)
    state.prev_lat, state.prev_lon = old_lat, old_lon
    if state.battery <= 5.0:
        state.status = "degraded"
    elif state.battery <= 0.0:
        state.status = "offline"
    else:
        state.status = "online"
    state.sequence_number += 1
    return state


def snapshot_payload(
    state: DeviceState,
    *,
    radio: RadioKpis | dict | None = None,
    measured: MeasuredKpis | dict | None = None,
) -> TelemetryPayload:
    radio_model = None
    if radio is not None:
        radio_model = radio if isinstance(radio, RadioKpis) else RadioKpis.model_validate(radio)
    measured_model = None
    if measured is not None:
        measured_model = (
            measured
            if isinstance(measured, MeasuredKpis)
            else MeasuredKpis.model_validate(measured)
        )
    return TelemetryPayload(
        device_id=state.device_id,
        timestamp=datetime.now(UTC),
        temperature=round(state.temperature, 3),
        humidity=round(state.humidity, 3),
        battery=round(state.battery, 3),
        latitude=round(state.latitude, 6),
        longitude=round(state.longitude, 6),
        status=state.status,  # type: ignore[arg-type]
        source_ip=state.source_ip,
        schema_version=SCHEMA_VERSION,
        sequence_number=state.sequence_number,
        radio=radio_model,
        measured=measured_model,
    )
