# Architecture

## Components

| Component | Where it runs | Purpose |
|---|---|---|
| UE simulator | **Host** Python (project `.venv`) | N virtual devices; MQTT publish with optional 5G source bind |
| Mosquitto | Compose, `172.31.240.10` | Authenticated MQTT, persistence |
| Backend consumer | Compose, `172.31.240.13` | Subscribe, validate, batch insert, health API |
| TimescaleDB | Compose, `172.31.240.11` | `devices`, `telemetry` hypertable, `dead_letter` |
| Grafana | Compose, `172.31.240.12` | Provisioned dashboards |
| Kafka / RabbitMQ | Compose profile `extras` | Optional bridges, disabled by default |

The UE simulator is **not** started by default compose. Binding `uesimtunN` requires the host network namespace. Compose never uses `network_mode: host`. The optional `ue-simulator/Dockerfile` is **direct-mode only**.

## Data path (5G)

1. UERANSIM `nr-ue` (managed outside this repo) creates `uesimtunN` with a UE address.
2. Operator copies that address into `config/devices.yaml` (`source_ip`, `interface`).
3. Simulator calls `socket.bind((source_ip, 0))` then TCP-connects to `MQTT_HOST:MQTT_PORT`.
4. Packets egress the UE tunnel, through the existing UPF toward the data network.
5. Mosquitto is reached either because the DN already includes the Docker-published host port, or after **manual** least-invasive forwarding documented in `manual-host-changes.md` (not applied by scripts).
6. Consumer stores rows; Grafana reads TimescaleDB on the compose network.

## Data path (direct)

Simulator uses the default host route to `127.0.0.1:18830`. No tunnel bind.

## Storage

Single schema file: `config/schema.sql`.

- `telemetry` hypertable, index `(device_id, timestamp DESC)`, linear-power RF columns, views `v_rsrp_avg` / `v_kpi_modeled` / `v_kpi_measured`
- Echo RTT hypertable; `device_flow_kpis` for PDR/gap/dup/reorder
- compression after 7 days, retention 30 days (example policies)
- malformed MQTT payloads → `dead_letter` (consumer does not crash)

## Health

- `GET /health` — process up
- `GET /ready` — DB ping + MQTT connected
- `GET /metrics` — counters (ok, dead letter, batches, bridges)

## Failure handling

- MQTT keepalive default 120s, exponential reconnect backoff (1s…60s)
- Consumer validation errors increment dead-letter counters
- Kafka/AMQP init/publish errors are logged; ingest continues
