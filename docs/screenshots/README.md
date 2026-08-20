# Screenshots

PNGs here are for the GitHub README. They are **not** required for CI. Captions below match what the captures actually show.

**Do not claim** NTN/ATG, a 50–100 UE fleet, or UERANSIM `uesimtun` user-plane tunnels in these shots.

Keep images unannotated with internal hostnames if you share the repo publicly.

## On disk

| File | Status | Honest caption |
|---|---|---|
| `simulator-direct-mqtt.png` | **Copied** | Host terminal: `docker compose up --build` brought up the **consumer** and **Grafana** for project `5g-iot-telemetry`. Then `python -m ue_simulator` with **`BIND_MODE=direct`** (not 5G user plane), **`MQTT_HOST=127.0.0.1`**, **`MQTT_PORT=18830`**. **Two simulated devices** (`iot-001`, `iot-002`) connected to MQTT (`mqtt_connected` Success, `bind_mode` direct). Radio: **RF modeled**, profile **`terrestrial_uma`**, not measured. |
| `grafana-overview.png` | **Copied** | Grafana **MEASURED (application / path)** view: temperature, humidity, battery, message rate, online/offline, MQTT echo RTT for **iot-001** and **iot-002**. Application-path metrics (direct bind or user plane packets + consumer), **not** the radio model. |
| `grafana-geomap.png` | Placeholder | Geomap panel with drifting points (attach when you have a clean crop). |
| `grafana-status.png` | Placeholder | Device online/offline table and message rate (if not already covered by overview). |
| `grafana-kpis.png` | Placeholder | Modeled vs measured KPI dashboard with the modeled disclaimer visible. |

## Terminal snap details (`simulator-direct-mqtt.png`)

What the capture shows:

- `docker compose up --build` for compose project **5g-iot-telemetry**
- Image **5g-iot-telemetry-consumer** built; **consumer** and **grafana** started
- `cd ~/5g-iot-telemetry`, `source .venv/bin/activate`
- `BIND_MODE=direct`, `MQTT_HOST=127.0.0.1`, `MQTT_PORT=18830`
- `python -m ue_simulator`
- `radio_model_loaded terrestrial_uma` (RF modeled, not measured)
- `simulator_started devices: 2`
- `iot-001` and `iot-002` `mqtt_connected` Success, `bind_mode` direct

What it does **not** show: 5G user-plane bind, UERANSIM tunnels, NTN/ATG, or a large UE count.

See also [docs/GITHUB_SCREENSHOTS.md](../GITHUB_SCREENSHOTS.md).
