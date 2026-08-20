from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock


@dataclass
class Counters:
    messages_ok: int = 0
    messages_dead_letter: int = 0
    batches_flushed: int = 0
    status_ok: int = 0
    mqtt_reconnects: int = 0
    bridge_kafka_ok: int = 0
    bridge_kafka_err: int = 0
    bridge_amqp_ok: int = 0
    bridge_amqp_err: int = 0
    mqtt_connected: bool = False
    _lock: Lock = field(default_factory=Lock, repr=False)

    def inc(self, name: str, amount: int = 1) -> None:
        with self._lock:
            setattr(self, name, getattr(self, name) + amount)

    def set_mqtt(self, connected: bool) -> None:
        with self._lock:
            self.mqtt_connected = connected
            if not connected:
                self.mqtt_reconnects += 1

    def snapshot(self) -> dict[str, int | bool]:
        with self._lock:
            return {
                "messages_ok": self.messages_ok,
                "messages_dead_letter": self.messages_dead_letter,
                "batches_flushed": self.batches_flushed,
                "status_ok": self.status_ok,
                "mqtt_reconnects": self.mqtt_reconnects,
                "bridge_kafka_ok": self.bridge_kafka_ok,
                "bridge_kafka_err": self.bridge_kafka_err,
                "bridge_amqp_ok": self.bridge_amqp_ok,
                "bridge_amqp_err": self.bridge_amqp_err,
                "mqtt_connected": self.mqtt_connected,
            }
