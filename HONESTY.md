# Honesty contract — 5G IoT telemetry

This lab is an **isolated MQTT telemetry demo** (Mosquitto, TimescaleDB, Grafana, host Python simulator). It can optionally bind sockets to an **existing** UERANSIM tunnel. It is **not** an ATG/NTN RAN, and it does **not** install a 5G core.

## Captured demo (screenshots)

| Item | Fact |
|---|---|
| Bind | `BIND_MODE=direct` — **not** 5G user plane |
| MQTT | `127.0.0.1:18830` |
| Devices | **2** (`iot-001`, `iot-002`) |
| RF | Modeled (`terrestrial_uma`), not measured |
| Grafana | Host port **13000**; application-path panels |

`DEVICE_COUNT` may start a larger **direct** fleet. That still is not `uesimtun` traffic.

## Isolation

Scripts only touch compose project `5g-iot-telemetry`. They do not edit `/etc/open5gs`, run Helm against Open5GS, kill `nr-gnb`/`nr-ue`, or `docker system prune`.

See `docs/isolation-and-safety.md`. Operator honesty notes live in the private companion repo `5g-iot-telemetry-scripts`.
