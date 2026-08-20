# Kafka and RabbitMQ extensions

Bridges are **implemented** in `backend-consumer/src/backend_consumer/bridges/` and **disabled** by default.

## Enable

1. In `.env`:

```bash
ENABLE_KAFKA_BRIDGE=true
ENABLE_AMQP_BRIDGE=true
```

2. Start extras **in this compose project only**:

```bash
docker compose -p 5g-iot-telemetry --env-file .env --profile extras up -d kafka rabbitmq
```

or `make extras-up`.

3. Recreate the consumer so it sees the flags:

```bash
docker compose -p 5g-iot-telemetry --env-file .env up -d --force-recreate consumer
```

If brokers are down, the consumer **keeps ingesting MQTT**; bridge errors are counters + logs.

## Host ports

- Kafka external listener: **19092**
- RabbitMQ AMQP: **15672** (container 5672)
- RabbitMQ management UI: **15673** (container 15672)

## Topics / exchange

- Kafka topic: `iot.telemetry` (`KAFKA_TOPIC`)
- AMQP exchange: `iot` topic exchange, routing key `telemetry`

Do not confuse these with the MQTT topic tree in `docs/topics.md`.
