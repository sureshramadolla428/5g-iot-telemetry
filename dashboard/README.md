# Grafana dashboards (this compose stack only)

Provisioned from `dashboards/` into Grafana folder **5G IoT**. Datasource uid **`timescaledb`** (Postgres/Timescale).

## Open them

1. Start the stack (`docker compose up -d`). Grafana is **http://127.0.0.1:13000** (host; container still listens on 3000).
2. Login: `GF_SECURITY_ADMIN_USER` / `GF_SECURITY_ADMIN_PASSWORD` (see `.env.example`).
3. Dashboards → folder **5G IoT**, or go directly:
   - [5G IoT Lab Demo](http://127.0.0.1:13000/d/5g-iot-lab-demo) — presentation: honesty banner, live KPI strip, hero geomap, MEASURED sensors, MODELED RF (collapsed-style rows).
   - [5G IoT KPIs (modeled vs measured)](http://127.0.0.1:13000/d/5g-iot-kpis) — NTN-style honesty: MEASURED path KPIs vs MODELED radio (not OTA).
   - [5G IoT Ops](http://127.0.0.1:13000/d/5g-iot-ops) — super-ops live counters (rate, online, PDR, RTT, lag, jitter, gaps) plus modeled RSRP/CQI.

Template variable **`device_id`** is multi-select with **Include all**. Time range default **last 15m**, refresh **5s**, **liveNow**.

## Files

| File | uid | Title |
| --- | --- | --- |
| `dashboards/iot-overview.json` | `5g-iot-lab-demo` | 5G IoT Lab Demo |
| `dashboards/iot-kpis.json` | `5g-iot-kpis` | 5G IoT KPIs (modeled vs measured) |
| `dashboards/iot-ops.json` | `5g-iot-ops` | 5G IoT Ops |
| `provisioning/datasources/datasource.yml` | TimescaleDB uid `timescaledb` | |
| `provisioning/dashboards/dashboards.yml` | file provider → folder **5G IoT** | |

Queries use IoT tables only: `telemetry`, `echo_rtt`, `device_flow_kpis`, `devices`. RF columns (`rsrp_dbm`, …) are **modeled** when present; SQL uses `IS NOT NULL`, not `radio_source = 'modeled'`.

## Permissions (Grafana user 472)

The Grafana container runs as **uid 472**. If provisioned dashboards are empty or Grafana logs `permission denied` on `/var/lib/grafana/dashboards`, make the tree world-readable:

```bash
chmod -R a+rX dashboard
```

The operator refresh helper in private repo `5g-iot-telemetry-scripts` runs that chmod before recreating Grafana.

Screenshot placeholders: `docs/screenshots/`.
