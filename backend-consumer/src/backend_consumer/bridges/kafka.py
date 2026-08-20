from __future__ import annotations

import logging

from backend_consumer.models.counters import Counters

LOG = logging.getLogger("backend_consumer.bridges.kafka")


class KafkaBridge:
    def __init__(self, bootstrap: str, topic: str, enabled: bool, counters: Counters) -> None:
        self._topic = topic
        self._enabled = enabled
        self._counters = counters
        self._producer = None
        if not enabled:
            LOG.info("kafka bridge disabled")
            return
        try:
            from kafka import KafkaProducer

            self._producer = KafkaProducer(
                bootstrap_servers=bootstrap.split(","),
                value_serializer=lambda v: v if isinstance(v, bytes) else str(v).encode(),
                retries=3,
                request_timeout_ms=10000,
                linger_ms=50,
            )
            LOG.info("kafka bridge enabled topic=%s bootstrap=%s", topic, bootstrap)
        except Exception as exc:
            LOG.error("kafka bridge init failed (consumer continues): %s", exc)
            self._producer = None

    def publish(self, key: str, payload: str) -> None:
        if not self._enabled or self._producer is None:
            return
        try:
            self._producer.send(self._topic, key=key.encode(), value=payload.encode())
            self._counters.inc("bridge_kafka_ok")
        except Exception as exc:
            LOG.warning("kafka publish failed: %s", exc)
            self._counters.inc("bridge_kafka_err")

    def close(self) -> None:
        if self._producer is not None:
            try:
                self._producer.flush(timeout=5)
                self._producer.close()
            except Exception:
                pass
