# 5G integration (UERANSIM user plane)

This demo **does not** install or reconfigure Open5GS, MongoDB, or UERANSIM. It assumes a working UE tunnel on the same Linux host where you run `python -m ue_simulator`.

## Dedicated identities (guidance only)

Create extra subscribers **yourself** in your existing core, using a range that will not collide with NTN/A2G/eMBB test UEs. Suggested lab convention (adjust to your PLMN):

| Field | Suggested dedicated value | Notes |
|---|---|---|
| IMSI range | `999700000000301`–`999700000000320` | Pick a block unused by other labs |
| DNN / APN | `iot` | Separate from `internet` / NTN DNNs if possible |
| SST / SD | eMBB or a dedicated IoT SST you already use | Do not edit slice YAML from this repo |
| UE count | Match `config/devices.yaml` entries | One tunnel IP per `device_id` |

**Do not** run subscriber-import scripts from this repository — there are none on purpose.

## Explicit source bind

`BIND_MODE=5g` (default in `.env.example`) requires every device to have a real IPv4 `source_ip`.

The simulator will **exit** if `source_ip` is missing, `auto`, `first`, or `any`. It will **not** pick `uesimtun0` for you.

```yaml
devices:
  - device_id: iot-001
    interface: uesimtun0
    source_ip: 10.45.0.2    # YOUR address from: ip -br addr show uesimtun0
```

Discover tunnels (read-only): `ip -br addr` / `ip -br link | grep uesimtun`. An operator helper lives in private repo `5g-iot-telemetry-scripts`.

## MQTT target from the UE

Set `MQTT_HOST` / `MQTT_PORT` in `.env` to whatever IPv4:port the **UE user-plane** can reach. Typical patterns:

1. Host DN address already routed from the UPF, with Docker publishing `18830` on that host.
2. A small **manual** DNAT/FORWARD documented in `manual-host-changes.md` (you apply it; scripts do not).

Never commit a lab-specific IP into git.

## High RTT / loss

Keepalives (`MQTT_KEEPALIVE=120`), connect timeouts, and exponential reconnect are enabled in the publisher. QoS 1 is used for telemetry and status.

## Direct fallback

```bash
export BIND_MODE=direct MQTT_HOST=127.0.0.1 MQTT_PORT=18830
python -m ue_simulator
```

Direct mode skips `socket.bind` of a UE address so you can demo Grafana without a core.
