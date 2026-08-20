from __future__ import annotations

import logging
import signal
import sys
import threading

import uvicorn

from backend_consumer.app import create_app
from backend_consumer.bridges.amqp import AmqpBridge
from backend_consumer.bridges.kafka import KafkaBridge
from backend_consumer.config import load_settings
from backend_consumer.models.counters import Counters
from backend_consumer.mqtt.subscriber import TelemetrySubscriber
from backend_consumer.storage.timescaledb import TimescaleStorage

LOG = logging.getLogger("backend_consumer")


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format='{"logger":"%(name)s","level":"%(levelname)s","msg":"%(message)s"}',
    )
    settings = load_settings()
    counters = Counters()
    storage = TimescaleStorage(settings.dsn)
    kafka = KafkaBridge(
        settings.kafka_bootstrap_servers,
        settings.kafka_topic,
        settings.enable_kafka_bridge,
        counters,
    )
    amqp = AmqpBridge(
        settings.amqp_url,
        settings.amqp_exchange,
        settings.amqp_routing_key,
        settings.enable_amqp_bridge,
        counters,
    )

    def on_telemetry(payload, raw: str) -> None:
        kafka.publish(payload.device_id, raw)
        amqp.publish(payload.device_id, raw)

    subscriber = TelemetrySubscriber(
        host=settings.mqtt_host,
        port=settings.mqtt_port,
        username=settings.mqtt_username,
        password=settings.mqtt_password,
        keepalive=settings.mqtt_keepalive,
        qos=settings.mqtt_qos,
        client_id=settings.consumer_client_id,
        storage=storage,
        counters=counters,
        batch_size=settings.batch_size,
        batch_flush_seconds=settings.batch_flush_seconds,
        dead_letter_max=settings.dead_letter_max_payload_bytes,
        on_telemetry=on_telemetry,
    )
    subscriber.start()
    app = create_app(counters, storage)
    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host=settings.consumer_bind_host,
            port=settings.consumer_bind_port,
            log_level="info",
        )
    )

    def _stop(signum: int, _frame: object) -> None:
        LOG.info("signal %s, shutting down", signum)
        server.should_exit = True

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    thread = threading.Thread(target=server.run, name="http", daemon=True)
    thread.start()
    try:
        thread.join()
    finally:
        subscriber.stop()
        kafka.close()
        amqp.close()
        storage.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
