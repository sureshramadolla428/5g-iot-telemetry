from __future__ import annotations

import json
import logging
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime

import paho.mqtt.client as mqtt
from pydantic import ValidationError

from backend_consumer.models.counters import Counters
from backend_consumer.mqtt.client import make_client
from backend_consumer.storage.base import Storage
from iot_schema.payload import DeviceStatusPayload, EchoPayload, TelemetryPayload
from iot_schema.rows import attach_rfc3550_jitter
from iot_schema.topics import (
    ECHO_SUFFIX,
    STATUS_SUFFIX,
    SUBSCRIBE_FILTERS,
    TELEMETRY_SUFFIX,
    TopicError,
    echo_topic,
    parse_device_topic,
)
from metrics.goodput import SequenceStats, message_rate_hz
from metrics.latency import Rfc3550Jitter

LOG = logging.getLogger("backend_consumer.mqtt")


class TelemetrySubscriber:
    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str,
        password: str,
        keepalive: int,
        qos: int,
        client_id: str,
        storage: Storage,
        counters: Counters,
        batch_size: int,
        batch_flush_seconds: float,
        dead_letter_max: int,
        on_telemetry: Callable[[TelemetryPayload, str], None] | None = None,
    ) -> None:
        self._storage = storage
        self._counters = counters
        self._qos = qos
        self._batch_size = batch_size
        self._batch_flush_seconds = batch_flush_seconds
        self._dead_letter_max = dead_letter_max
        self._on_telemetry = on_telemetry
        self._buffer: list[TelemetryPayload] = []
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._seq: dict[str, SequenceStats] = {}
        self._first_ts: dict[str, float] = {}
        self._jitter: dict[str, Rfc3550Jitter] = {}
        self.client = make_client(client_id, username, password)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self._host = host
        self._port = port
        self._keepalive = keepalive

    def start(self) -> None:
        self.client.connect(self._host, self._port, keepalive=self._keepalive)
        self.client.loop_start()
        threading.Thread(target=self._flusher, name="batch-flush", daemon=True).start()

    def stop(self) -> None:
        self._stop.set()
        self._flush_locked(force=True)
        self.client.loop_stop()
        self.client.disconnect()

    def _on_connect(self, client, userdata, flags, reason_code, properties=None) -> None:  # noqa: ANN001
        LOG.info("mqtt connected rc=%s", reason_code)
        self._counters.set_mqtt(True)
        for filt in SUBSCRIBE_FILTERS:
            client.subscribe(filt, qos=self._qos)

    def _on_disconnect(self, client, userdata, flags, reason_code, properties=None) -> None:  # noqa: ANN001
        LOG.warning("mqtt disconnected rc=%s", reason_code)
        self._counters.set_mqtt(False)

    def _on_message(self, client, userdata, msg: mqtt.MQTTMessage) -> None:  # noqa: ANN001
        raw = msg.payload.decode("utf-8", errors="replace")
        clipped = raw[: self._dead_letter_max]
        try:
            device_id, kind = parse_device_topic(msg.topic)
        except TopicError as exc:
            self._dead(msg.topic, f"topic: {exc}", clipped)
            return
        if kind == TELEMETRY_SUFFIX:
            self._handle_telemetry(msg.topic, clipped)
        elif kind == STATUS_SUFFIX:
            self._handle_status(msg.topic, device_id, clipped)
        elif kind == ECHO_SUFFIX:
            self._handle_echo(device_id, clipped)

    def _handle_telemetry(self, topic: str, raw: str) -> None:
        try:
            payload = TelemetryPayload.model_validate_json(raw)
        except (ValidationError, json.JSONDecodeError, ValueError) as exc:
            self._dead(topic, f"telemetry_validation: {exc}", raw)
            return
        if payload.sequence_number is not None:
            self._track_sequence(payload.device_id, payload.sequence_number)
        tracker = self._jitter.setdefault(payload.device_id, Rfc3550Jitter())
        attach_rfc3550_jitter(payload, tracker, datetime.now(UTC))
        with self._lock:
            self._buffer.append(payload)
            if len(self._buffer) >= self._batch_size:
                self._flush_unlocked()
        if self._on_telemetry:
            try:
                self._on_telemetry(payload, raw)
            except Exception as exc:
                LOG.warning("bridge callback failed: %s", exc)
        self._counters.inc("messages_ok")

    def _handle_status(self, topic: str, device_id: str, raw: str) -> None:
        try:
            payload = DeviceStatusPayload.model_validate_json(raw)
        except (ValidationError, json.JSONDecodeError, ValueError) as exc:
            self._dead(topic, f"status_validation: {exc}", raw)
            return
        if payload.device_id != device_id:
            self._dead(topic, "device_id mismatch vs topic", raw)
            return
        try:
            self._storage.write_status(payload)
            self._counters.inc("status_ok")
        except Exception as exc:
            LOG.error("status persist failed: %s", exc)
            self._dead(topic, f"status_persist: {exc}", raw)

    def _dead(self, topic: str | None, reason: str, raw: str) -> None:
        LOG.warning("dead_letter topic=%s reason=%s", topic, reason)
        try:
            self._storage.write_dead_letter(topic, reason, raw)
        except Exception as exc:
            LOG.error("dead_letter persist failed: %s", exc)
        self._counters.inc("messages_dead_letter")

    def _handle_echo(self, device_id: str, raw: str) -> None:
        try:
            echo = EchoPayload.model_validate_json(raw)
        except (ValidationError, json.JSONDecodeError, ValueError) as exc:
            self._dead(echo_topic(device_id), f"echo_validation: {exc}", raw)
            return
        if echo.role != "ping":
            return
        now_ms = time.time() * 1000.0
        reply = EchoPayload(
            device_id=device_id,
            role="pong",
            sequence_number=echo.sequence_number,
            t_tx_unix_ms=echo.t_tx_unix_ms,
            t_rx_unix_ms=now_ms,
        )
        self.client.publish(
            echo_topic(device_id), reply.model_dump_json(), qos=self._qos, retain=False
        )
        rtt = now_ms - echo.t_tx_unix_ms
        try:
            self._storage.write_echo_rtt(device_id, echo.sequence_number, rtt)
        except Exception as exc:
            LOG.warning("echo_rtt persist failed: %s", exc)

    def _track_sequence(self, device_id: str, seq: int) -> None:
        stats = self._seq.setdefault(device_id, SequenceStats())
        stats.observe(seq)
        now = time.time()
        start = self._first_ts.setdefault(device_id, now)
        elapsed = max(now - start, 1e-6)
        try:
            self._storage.upsert_flow_kpis(
                device_id,
                {
                    "received": stats.received,
                    "duplicates": stats.duplicates,
                    "gaps": stats.gaps,
                    "reorders": stats.reorders,
                    "pdr": stats.pdr(),
                    "plr": stats.plr(),
                    "msg_rate_hz": message_rate_hz(stats.received, elapsed),
                    "last_seq": stats.last_seq,
                },
            )
        except Exception as exc:
            LOG.warning("flow kpi persist failed: %s", exc)

    def _flusher(self) -> None:
        while not self._stop.wait(self._batch_flush_seconds):
            self._flush_locked(force=True)

    def _flush_locked(self, force: bool = False) -> None:
        with self._lock:
            if force or len(self._buffer) >= self._batch_size:
                self._flush_unlocked()

    def _flush_unlocked(self) -> None:
        if not self._buffer:
            return
        batch = self._buffer
        self._buffer = []
        try:
            self._storage.write_telemetry_batch(batch)
            self._counters.inc("batches_flushed")
        except Exception as exc:
            LOG.error("batch persist failed (%s rows): %s", len(batch), exc)
            for row in batch:
                self._dead(
                    f"iot/devices/{row.device_id}/telemetry",
                    f"batch_persist: {exc}",
                    row.model_dump_json(),
                )
