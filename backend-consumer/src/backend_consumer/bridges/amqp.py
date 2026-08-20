from __future__ import annotations

import logging

from backend_consumer.models.counters import Counters

LOG = logging.getLogger("backend_consumer.bridges.amqp")


class AmqpBridge:
    def __init__(
        self, url: str, exchange: str, routing_key: str, enabled: bool, counters: Counters
    ) -> None:
        self._url = url
        self._exchange = exchange
        self._routing_key = routing_key
        self._enabled = enabled
        self._counters = counters
        self._connection = None
        self._channel = None
        if not enabled:
            LOG.info("amqp bridge disabled")
            return
        try:
            import pika

            params = pika.URLParameters(url)
            params.socket_timeout = 10
            params.blocked_connection_timeout = 10
            self._connection = pika.BlockingConnection(params)
            self._channel = self._connection.channel()
            self._channel.exchange_declare(exchange=exchange, exchange_type="topic", durable=True)
            LOG.info("amqp bridge enabled exchange=%s", exchange)
        except Exception as exc:
            LOG.error("amqp bridge init failed (consumer continues): %s", exc)
            self._connection = None
            self._channel = None

    def publish(self, key: str, payload: str) -> None:
        if not self._enabled or self._channel is None:
            return
        try:
            self._channel.basic_publish(
                exchange=self._exchange,
                routing_key=self._routing_key or key,
                body=payload.encode(),
            )
            self._counters.inc("bridge_amqp_ok")
        except Exception as exc:
            LOG.warning("amqp publish failed: %s", exc)
            self._counters.inc("bridge_amqp_err")

    def close(self) -> None:
        if self._connection is not None:
            try:
                self._connection.close()
            except Exception:
                pass
