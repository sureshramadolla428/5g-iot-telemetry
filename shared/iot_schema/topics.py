"""MQTT topic helpers. Canonical pattern: iot/devices/{device_id}/{kind}."""

from __future__ import annotations

TELEMETRY_SUFFIX = "telemetry"
STATUS_SUFFIX = "status"
ECHO_SUFFIX = "echo"
TOPIC_PREFIX = ("iot", "devices")
KINDS = (TELEMETRY_SUFFIX, STATUS_SUFFIX, ECHO_SUFFIX)
SUBSCRIBE_FILTERS = (
    "iot/devices/+/telemetry",
    "iot/devices/+/status",
    "iot/devices/+/echo",
)


class TopicError(ValueError):
    """Raised when a topic does not match the canonical pattern."""


def telemetry_topic(device_id: str) -> str:
    _check_device_id(device_id)
    return f"iot/devices/{device_id}/telemetry"


def status_topic(device_id: str) -> str:
    _check_device_id(device_id)
    return f"iot/devices/{device_id}/status"


def echo_topic(device_id: str) -> str:
    _check_device_id(device_id)
    return f"iot/devices/{device_id}/echo"


def parse_device_topic(topic: str) -> tuple[str, str]:
    """Return (device_id, kind) where kind is telemetry, status, or echo."""
    parts = topic.split("/")
    if (
        len(parts) != 4
        or parts[0] != TOPIC_PREFIX[0]
        or parts[1] != TOPIC_PREFIX[1]
        or parts[3] not in KINDS
        or not parts[2]
    ):
        raise TopicError(f"unsupported topic: {topic!r}")
    return parts[2], parts[3]


def _check_device_id(device_id: str) -> None:
    if not device_id or "/" in device_id or "+" in device_id or "#" in device_id:
        raise TopicError(f"invalid device_id: {device_id!r}")
