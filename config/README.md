# Config

| File | Purpose |
|---|---|
| `schema.sql` | TimescaleDB schema (single DB source of truth) |
| `payload.schema.json` | JSON schema for telemetry |
| `devices.yaml.example` | Per-device interface/source_ip map |
| `mosquitto/passwd.example` | Password file template (runtime file is generated) |
| `radio_model.yaml` | Terrestrial UMa defaults; NTN/A2G flags |
| `migrations/002_kpi.sql` | Additive KPI columns if v1 volume already exists |
