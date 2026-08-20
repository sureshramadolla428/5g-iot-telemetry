from __future__ import annotations

import pytest

from iot_schema.topics import TopicError, parse_device_topic, status_topic, telemetry_topic


def test_canonical_topics():
    assert telemetry_topic("iot-001") == "iot/devices/iot-001/telemetry"
    assert status_topic("iot-001") == "iot/devices/iot-001/status"
    from iot_schema.topics import echo_topic

    assert echo_topic("iot-001") == "iot/devices/iot-001/echo"


def test_parse_roundtrip():
    device_id, kind = parse_device_topic("iot/devices/iot-002/status")
    assert device_id == "iot-002"
    assert kind == "status"


@pytest.mark.parametrize(
    "topic",
    [
        "iot/devices/iot-001/other",
        "devices/iot-001/telemetry",
        "iot/device/iot-001/telemetry",
        "iot/devices//telemetry",
        "",
    ],
)
def test_parse_rejects_bad_topics(topic):
    with pytest.raises(TopicError):
        parse_device_topic(topic)


def test_device_id_cannot_contain_mqtt_wildcards():
    with pytest.raises(TopicError):
        telemetry_topic("iot/+/x")
