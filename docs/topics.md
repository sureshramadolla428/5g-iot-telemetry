# MQTT topics

Canonical pattern:

```
iot/devices/{device_id}/telemetry
iot/devices/{device_id}/status
iot/devices/{device_id}/echo
```

`device_id` is `[A-Za-z0-9._:-]+` and must not contain `/`, `+`, or `#`.

## Subscriptions (consumer)

- `iot/devices/+/telemetry`
- `iot/devices/+/status`
- `iot/devices/+/echo` (ping → pong for measured RTT; not retained)

## QoS

All demo publishers and the consumer use **QoS 1**.

## Retain and LWT

| Topic | Retain | LWT |
|---|---|---|
| `.../status` | yes | yes (`offline`, detail `last-will`) |
| `.../telemetry` | **no** | no |

On connect the simulator publishes `status=online` (retain). On SIGINT/SIGTERM it publishes `offline` then disconnects.
