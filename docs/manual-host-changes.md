# Manual host changes (optional, least invasive)

Scripts in this repo **do not** apply firewall or routing changes. Use this page only if the UE user-plane cannot reach Mosquitto on the published host port.

Goal: UE packets arriving on the N6/DN side of the **existing** UPF should hit Mosquitto listening on `127.0.0.1:${MQTT_HOST_PORT}` (default 18830) **or** on the host's DN interface.

## Preferred: no iptables

1. Bind Mosquitto via compose publish `18830:1883` (already done).
2. Set `MQTT_HOST` to a host IP that is **already** reachable from the UE DNN (often the same DN next-hop you use for internet UEs).
3. Confirm the UE source IP is on a `uesimtunN` address (`ip -br addr`). An operator tunnel-check helper lives in private repo `5g-iot-telemetry-scripts`.

## If you must DNAT (operator-applied)

Tag every rule with comment `5g-iot-telemetry` so rollback can remove **only** those rules.

Example pattern (replace interface and addresses yourself; do not copy lab IPs into git):

```bash
# Forward TCP 18830 from a DN-facing interface into the docker-proxy port.
# IFACE = your N6/DN interface name (NOT guessed by this repo)
sudo iptables -A INPUT -i "$IFACE" -p tcp --dport 18830 -m comment --comment 5g-iot-telemetry -j ACCEPT
sudo iptables -A FORWARD -p tcp --dport 18830 -m comment --comment 5g-iot-telemetry -j ACCEPT
```

Do **not** flush filter/nat tables. Do **not** masquerade all UE traffic. Do **not** change Open5GS `upf.yaml`.

## Rollback

Delete only rules whose comment is `5g-iot-telemetry` (operator helper in private repo `5g-iot-telemetry-scripts`). Requires the same `sudo` privileges you used to insert the rules.
