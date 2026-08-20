"""paho MQTT client factory with 5G-friendly keepalive/reconnect defaults."""

from __future__ import annotations

import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion


def make_client(client_id: str, username: str, password: str) -> mqtt.Client:
    client = mqtt.Client(
        callback_api_version=CallbackAPIVersion.VERSION2,
        client_id=client_id,
        protocol=mqtt.MQTTv311,
    )
    client.username_pw_set(username, password)
    client.reconnect_delay_set(min_delay=1, max_delay=60)
    return client
