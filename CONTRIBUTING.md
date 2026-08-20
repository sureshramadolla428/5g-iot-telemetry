# Contributing

Thank you for improving this isolated demo. Keep it safe for machines that already run Open5GS, UERANSIM, or NTN labs.

## Rules

1. Write files only inside this repository.
2. Do not add `network_mode: host`.
3. Compose commands must use `-p 5g-iot-telemetry`.
4. Do not add scripts that run `systemctl`, `iptables-apply`, `docker system prune`, or unscoped `compose down`.
5. Python dependencies: pin versions; install only in `.venv` (or CI's ephemeral environment).
6. No hardcoded lab machine IPs. Use `.env` and `config/devices.yaml`.
7. `BIND_MODE=5g` must keep failing if `source_ip` is missing/`auto`. Never auto-pick `uesimtun0`.

## Dev loop (Ubuntu)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
ruff check shared ue-simulator/src backend-consumer/src tests
pytest -q
```

## Pull requests

- Describe isolation impact (ports, subnets, host changes).
- Include tests for schema/bind/topic changes.
- Do not commit `.env` or `config/devices.yaml`.
