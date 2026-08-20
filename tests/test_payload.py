from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from iot_schema.payload import TelemetryPayload


def _ok(**overrides):
    base = {
        "device_id": "iot-001",
        "timestamp": datetime.now(UTC),
        "temperature": 21.5,
        "humidity": 40.0,
        "battery": 88.2,
        "latitude": 37.77,
        "longitude": -122.41,
        "status": "online",
    }
    base.update(overrides)
    return TelemetryPayload.model_validate(base)


def test_valid_payload_accepted():
    payload = _ok()
    assert payload.device_id == "iot-001"
    dumped = payload.model_dump_json()
    again = TelemetryPayload.model_validate_json(dumped)
    assert again.device_id == payload.device_id


def test_naive_timestamp_rejected():
    with pytest.raises(ValidationError):
        _ok(timestamp=datetime(2026, 8, 15, 12, 0, 0))


@pytest.mark.parametrize(
    "field,value",
    [
        ("temperature", -41),
        ("temperature", 86),
        ("humidity", -0.1),
        ("humidity", 100.1),
        ("battery", -1),
        ("battery", 101),
        ("latitude", -90.1),
        ("longitude", 181),
        ("status", "unknown"),
        ("device_id", ""),
        ("device_id", "bad/id"),
    ],
)
def test_out_of_range_rejected(field, value):
    with pytest.raises(ValidationError):
        _ok(**{field: value})


def test_malformed_json_rejected():
    with pytest.raises(ValidationError):
        TelemetryPayload.model_validate_json("{not-json")


def test_schema_version_default():
    payload = _ok()
    assert payload.schema_version == "1.1.0"
