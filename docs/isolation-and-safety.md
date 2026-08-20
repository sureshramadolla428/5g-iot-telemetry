# Isolation and safety

This project is designed to run on a workstation that already hosts Open5GS, UERANSIM, NTN emulation, or RAG labs.

## What scripts are allowed to do

- `docker compose -p 5g-iot-telemetry ...` only
- Create/use named volumes prefixed `5g-iot-telemetry_*`
- Create bridge network `5g-iot-telemetry_iot-net` on `DOCKER_SUBNET` (default `172.31.240.0/24`)
- Create `./.venv` and `./.env` inside this directory
- Read-only: `ss`, `ps` grep, `ip -br link/addr`, `docker network inspect`

## What they must never do

- Edit sibling directories (`github-ueransim-open5gs`, `5g-ntn-emulation-lab`, `URRANSIM_Open5gs`, `3GPP-RAG`, …)
- `systemctl` start/stop of core or RAN
- `kill` / `pkill` of `nr-gnb`, `nr-ue`, `open5gs-*`
- `iptables-restore` of a full table, or adding rules (except the optional human-applied commands in `manual-host-changes.md`)
- `docker system prune`, `docker compose down` without `-p 5g-iot-telemetry`
- `network_mode: host`
- Global `pip install` / `apt` on the developer machine (CI may install tools on GitHub runners)

## Port and subnet coexistence

Non-standard ports reduce collisions with Grafana `:3000`, Mosquitto `:1883`, Postgres `:5432`, Kafka `:9092`, and RabbitMQ `:5672/:15672`.

If Docker already has a network on `172.31.240.0/24`, change `DOCKER_SUBNET` in `.env` **before** the first compose `up`.

## Rollback

Operator rollback (private companion `5g-iot-telemetry-scripts`) deletes only iptables/ip6tables rules whose comment is `5g-iot-telemetry`. You can also delete matching rules by hand. Do **not** flush the whole table.
