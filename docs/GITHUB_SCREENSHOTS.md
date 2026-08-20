# GitHub screenshot notes (do not overclaim)

These captures are from a **direct bind** lab run: **two simulated devices** publishing MQTT to **localhost:18830**. The compose stack (consumer + Grafana) was up. RF is **modeled** (`terrestrial_uma`), not measured over the air.

**Do not claim:** NTN / ATG, 50–100 UEs, or UERANSIM user-plane tunnels.

## Files in `docs/screenshots/`

### `simulator-direct-mqtt.png` (on disk)

Terminal: compose build/up for `5g-iot-telemetry` (consumer + Grafana), then simulator in **direct** mode — **not** 5G user plane.

- MQTT: `127.0.0.1:18830`
- Devices: **2** (`iot-001`, `iot-002`), `mqtt_connected` Success, `bind_mode` direct
- `radio_model_loaded terrestrial_uma` (RF modeled, not measured)
- Consumer/Grafana compose stack came up

### `grafana-overview.png` (on disk)

Grafana measured application-path panels for the same **iot-001** / **iot-002** run (temp, humidity, battery, rate, status, MQTT echo RTT). Not radio-model KPIs.

### Placeholders (not copied yet)

- `grafana-geomap.png` — geomap
- `grafana-status.png` — status table if cropped separately
- `grafana-kpis.png` — modeled vs measured KPIs with disclaimer visible

Additional Grafana crops from the same session can be added here when a clean PNG is available.
