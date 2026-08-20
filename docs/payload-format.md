# Payload format

JSON schema: [`config/payload.schema.json`](../config/payload.schema.json).  
Pydantic: `shared/iot_schema/payload.py`.  
Formulas: [`docs/metrics-formulas.md`](metrics-formulas.md).  
`schema_version`: **1.1.0**.

## Telemetry example

```json
{
  "device_id": "iot-001",
  "schema_version": "1.1.0",
  "sequence_number": 42,
  "timestamp": "2026-08-15T18:01:02.123Z",
  "temperature": 22.5,
  "humidity": 41.0,
  "battery": 90.0,
  "latitude": 17.1234,
  "longitude": 78.1234,
  "status": "online",
  "source_ip": "10.45.0.2",
  "radio": {
    "source": "modeled",
    "disclaimer": "modeled — not radio-measured",
    "rsrp_dbm": -88.1,
    "rsrp_mw": 1.55e-9,
    "rsrq_db": -10.2,
    "sinr_db": 12.4,
    "cqi": 8
  },
  "measured": {
    "source": "measured",
    "rtt_ms": 27.4,
    "owd_ms": null,
    "jitter_rfc3550_ms": 1.2
  }
}
```

PHY fields inside `radio` **must** be `source=modeled` in this lab. `owd_ms` is null unless clocks are synced.

## Echo (measured RTT)

Topic `iot/devices/{id}/echo`:

```json
{ "device_id": "iot-001", "role": "ping", "sequence_number": 42, "t_tx_unix_ms": 1.0e12 }
```

Consumer replies with `role=pong` and `t_rx_unix_ms`.

Malformed messages still go to `dead_letter`.
