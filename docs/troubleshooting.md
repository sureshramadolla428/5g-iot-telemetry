# Troubleshooting

## Compose project name

Always `-p 5g-iot-telemetry`. If you accidentally started another project name, stop **that** project yourself; do not run an unscoped `docker compose down`.

## Port already allocated

Check `ss` (or equivalent) for 18830, 13000, 15432, 18080, 19092, 15672, 15673. Change the matching `*_HOST_PORT` in `.env`.

## Subnet overlap

Change `DOCKER_SUBNET` / `DOCKER_GATEWAY` before the first successful `up`. Docker will not move an existing network's subnet in place.

## `BIND_MODE=5g` fails immediately

Expected if `source_ip` is missing, `auto`, or not present on the host. Fill `config/devices.yaml` from `ip -br addr`. Never let the tool pick `uesimtun0`.

## Simulator runs but Grafana is empty

1. `curl -s http://127.0.0.1:18080/ready`
2. Publish one QoS 1 test message to `iot/devices/iot-001/telemetry` (operator helper is in private repo `5g-iot-telemetry-scripts`)
3. Confirm `.env` MQTT password matches what `mosquitto-init` used (recreate mosquitto if you changed secrets after first start: `docker compose -p 5g-iot-telemetry up -d --force-recreate mosquitto-init mosquitto`)
4. Timescale volume already initialized? `schema.sql` runs only on **empty** volume.

## UE cannot reach MQTT

See `docs/5g-integration.md` and `docs/manual-host-changes.md`. This project will not apply iptables for you.

## Mosquitto healthcheck fails

Init container must have written `/mosquitto/config/passwd`. Check `docker logs 5g-iot-telemetry-mosquitto-init`.

## Mosquitto: Invalid bridge configuration

Top-level `keepalive` / `keepalive_interval` / `retry_interval` are **bridge** options. This repo uses a standalone broker (`max_keepalive` only). After editing `config/mosquitto/mosquitto.conf`, the named volume `5g-iot-telemetry_mosquitto_config` may still hold the old file. Recreate **that volume only** (do **not** remove `5g-iot-telemetry_timescaledb`):

```bash
docker compose -p 5g-iot-telemetry stop mosquitto
docker compose -p 5g-iot-telemetry rm -f mosquitto mosquitto-init
docker volume rm 5g-iot-telemetry_mosquitto_config
docker compose -p 5g-iot-telemetry up -d --force-recreate mosquitto-init mosquitto
```

## Consumer crash-loop

`docker logs 5g-iot-telemetry-consumer`. Usual cause: Postgres not ready or wrong `POSTGRES_PASSWORD`. Malformed MQTT must **not** crash the process (dead letter).

## Accidental host rules

Remove only iptables rules tagged `5g-iot-telemetry` (operator helper in private repo `5g-iot-telemetry-scripts`). Do not flush the full table.
