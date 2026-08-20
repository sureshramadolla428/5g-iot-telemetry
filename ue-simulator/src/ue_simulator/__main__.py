"""Host-side UE MQTT publisher. Runs on the Linux host so it can bind uesimtunN."""

from __future__ import annotations

import json
import logging
import os
import random
import signal
import ssl
import sys
import threading
import time
from datetime import UTC, datetime
from typing import Any

import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion

from iot_schema.bind import BindError, create_source_bound_socket
from iot_schema.device_map import DeviceBind, load_device_map
from iot_schema.payload import DeviceStatusPayload, EchoPayload, MeasuredKpis
from iot_schema.telemetry import DeviceState, snapshot_payload, step_random_walk
from iot_schema.topics import echo_topic, status_topic, telemetry_topic
from metrics.constants import SCHEMA_VERSION
from metrics.iface_stats import read_interface_counters
from metrics.latency import Rfc3550Jitter, modeled_up_latency_ms, one_way_delay_ms
from metrics.mobility import bearing_deg, speed_mps
from metrics.radio.factory import build_radio_model, load_radio_config

LOG = logging.getLogger("ue_simulator")


def _device_index(device_id: str) -> int:
    digits = "".join(ch for ch in device_id if ch.isdigit())
    return max(int(digits), 1) if digits else 1


def _json_log(level: int, msg: str, **fields: Any) -> None:
    LOG.log(level, json.dumps({"msg": msg, **fields}, default=str, sort_keys=True))


def probe_bind(bind: DeviceBind, bind_mode: str) -> None:
    """Fail before MQTT connect if the source IP cannot be bound."""
    sock = create_source_bound_socket(
        bind.source_ip,
        bind_mode=bind_mode,
        device_id=bind.device_id,
        interface=bind.interface,
    )
    sock.close()


class DevicePublisher:
    def __init__(
        self,
        bind: DeviceBind,
        *,
        bind_mode: str,
        host: str,
        port: int,
        username: str,
        password: str,
        keepalive: int,
        qos: int,
        interval: float,
        rng: random.Random,
        radio_cfg: dict[str, Any],
        radio_model: Any,
    ) -> None:
        self.bind = bind
        self.bind_mode = bind_mode
        self.host = host
        self.port = port
        self.keepalive = keepalive
        self.qos = qos
        self.interval = interval
        self.rng = rng
        self.radio_cfg = radio_cfg
        self.radio_model = radio_model
        self.clocks_synced = bool(radio_cfg.get("clocks_synced", False))
        # Spread devices ~few hundred meters so the city geomap shows two dots.
        seed = _device_index(bind.device_id)
        self._device_index = seed
        self.state = DeviceState(
            device_id=bind.device_id,
            source_ip=bind.source_ip,
            latitude=17.1234 + (seed % 10) * 0.003,
            longitude=78.1234 + (seed // 10) * 0.003,
        )
        self._stop = threading.Event()
        self._backoff = 1.0
        self._rtt_ms: float | None = None
        self._jitter = Rfc3550Jitter()
        self._last_iface: dict[str, int] | None = None
        self.client = mqtt.Client(
            callback_api_version=CallbackAPIVersion.VERSION2,
            client_id=f"ue-{bind.device_id}",
            protocol=mqtt.MQTTv311,
        )
        self.client.username_pw_set(username, password)
        self.client.reconnect_delay_set(min_delay=1, max_delay=60)
        will = DeviceStatusPayload(
            device_id=bind.device_id,
            timestamp=datetime.now(UTC),
            status="offline",
            detail="last-will",
        )
        self.client.will_set(
            status_topic(bind.device_id),
            will.model_dump_json(),
            qos=qos,
            retain=True,
        )
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, reason_code, properties=None) -> None:  # noqa: ANN001
        _json_log(
            logging.INFO,
            "mqtt_connected",
            device_id=self.bind.device_id,
            source_ip=self.bind.source_ip,
            bind_mode=self.bind_mode,
            rc=str(reason_code),
        )
        self._backoff = 1.0
        client.subscribe(echo_topic(self.bind.device_id), qos=self.qos)
        online = DeviceStatusPayload(
            device_id=self.bind.device_id,
            timestamp=datetime.now(UTC),
            status="online",
            detail="connected",
        )
        client.publish(
            status_topic(self.bind.device_id),
            online.model_dump_json(),
            qos=self.qos,
            retain=True,
        )

    def _on_disconnect(self, client, userdata, flags, reason_code, properties=None) -> None:  # noqa: ANN001
        _json_log(
            logging.WARNING,
            "mqtt_disconnected",
            device_id=self.bind.device_id,
            rc=str(reason_code),
        )

    def _on_message(self, client, userdata, msg: mqtt.MQTTMessage) -> None:  # noqa: ANN001
        try:
            echo = EchoPayload.model_validate_json(msg.payload.decode("utf-8"))
        except Exception:
            return
        if echo.role != "pong":
            return
        now_ms = time.time() * 1000.0
        self._rtt_ms = now_ms - echo.t_tx_unix_ms
        self._jitter.update(echo.t_tx_unix_ms, now_ms)

    def start(self) -> None:
        threading.Thread(target=self._run, name=f"pub-{self.bind.device_id}", daemon=True).start()

    def stop(self) -> None:
        self._stop.set()
        try:
            offline = DeviceStatusPayload(
                device_id=self.bind.device_id,
                timestamp=datetime.now(UTC),
                status="offline",
                detail="shutdown",
            )
            self.client.publish(
                status_topic(self.bind.device_id),
                offline.model_dump_json(),
                qos=self.qos,
                retain=True,
            )
            time.sleep(0.2)
            self.client.loop_stop()
            self.client.disconnect()
        except Exception:
            _json_log(logging.WARNING, "shutdown_publish_failed", device_id=self.bind.device_id)

    def _connect_with_backoff(self) -> None:
        bind_address = self.bind.source_ip or ""
        while not self._stop.is_set():
            try:
                probe_bind(self.bind, self.bind_mode)
                _json_log(
                    logging.INFO,
                    "mqtt_connect_attempt",
                    device_id=self.bind.device_id,
                    host=self.host,
                    port=self.port,
                    bind_address=bind_address or None,
                )
                self.client.connect(
                    self.host,
                    self.port,
                    keepalive=self.keepalive,
                    bind_address=bind_address,
                    bind_port=0,
                )
                self.client.socket().settimeout(max(self.keepalive, 30))
                self.client.loop_start()
                return
            except (OSError, ssl.SSLError, BindError, TimeoutError, ValueError) as exc:
                _json_log(
                    logging.ERROR,
                    "mqtt_connect_failed",
                    device_id=self.bind.device_id,
                    error=str(exc),
                    backoff=self._backoff,
                )
                if self._stop.wait(self._backoff):
                    return
                self._backoff = min(self._backoff * 2.0, 60.0)

    def _measured(self) -> MeasuredKpis:
        iface = None
        if self.bind.interface:
            iface = read_interface_counters(self.bind.interface)
            self._last_iface = iface
        speed = bearing = None
        if (
            self.state.prev_lat is not None
            and self.state.prev_lon is not None
            and self.interval > 0
        ):
            speed = speed_mps(
                self.state.prev_lat,
                self.state.prev_lon,
                self.state.latitude,
                self.state.longitude,
                self.interval,
            )
            bearing = bearing_deg(
                self.state.prev_lat,
                self.state.prev_lon,
                self.state.latitude,
                self.state.longitude,
            )
        rtt = self._rtt_ms
        return MeasuredKpis(
            rtt_ms=rtt,
            owd_ms=one_way_delay_ms(rtt, self.clocks_synced) if rtt is not None else None,
            jitter_rfc3550_ms=self._jitter.jitter,
            iface_rx_bytes=iface["rx_bytes"] if iface else None,
            iface_tx_bytes=iface["tx_bytes"] if iface else None,
            iface_rx_packets=iface["rx_packets"] if iface else None,
            iface_tx_packets=iface["tx_packets"] if iface else None,
            speed_mps=speed,
            bearing_deg=bearing,
        )

    def _radio_kpis(self) -> dict[str, Any]:
        cfg = dict(self.radio_cfg)
        base_d = float(cfg.get("distance_2d_m", 400.0))
        cfg["distance_2d_m"] = base_d + (self._device_index % 25) * 6.0
        snap = self.radio_model.snapshot(cfg)
        dist = float(cfg.get("distance_2d_m", 400.0))
        lat = modeled_up_latency_ms(
            t_proc_ms=float(self.radio_cfg.get("t_proc_ms", 4.0)),
            t_queue_ms=float(self.radio_cfg.get("t_queue_ms", 2.0)),
            t_tx_ms=float(self.radio_cfg.get("t_tx_ms", 0.5)),
            distance_m=dist,
        )
        budget = float(self.radio_cfg.get("latency_budget_ms", 50.0))
        snap["l_up_ms"] = lat["l_up_ms"]
        snap["t_prop_ms"] = lat["t_prop_ms"]
        snap["latency_budget_pct"] = 100.0 * lat["l_up_ms"] / budget
        return snap

    def _run(self) -> None:
        self._connect_with_backoff()
        while not self._stop.is_set():
            step_random_walk(self.state, self.rng)
            payload = snapshot_payload(
                self.state, radio=self._radio_kpis(), measured=self._measured()
            )
            try:
                ping = EchoPayload(
                    device_id=self.bind.device_id,
                    role="ping",
                    sequence_number=self.state.sequence_number,
                    t_tx_unix_ms=time.time() * 1000.0,
                )
                self.client.publish(
                    echo_topic(self.bind.device_id),
                    ping.model_dump_json(),
                    qos=self.qos,
                    retain=False,
                )
                info = self.client.publish(
                    telemetry_topic(self.bind.device_id),
                    payload.model_dump_json(),
                    qos=self.qos,
                    retain=False,
                )
                if info.rc != mqtt.MQTT_ERR_SUCCESS:
                    raise OSError(f"publish rc={info.rc}")
            except Exception as exc:
                _json_log(
                    logging.ERROR,
                    "telemetry_publish_failed",
                    device_id=self.bind.device_id,
                    error=str(exc),
                )
            self._stop.wait(self.interval)


def _env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if value is None:
        raise BindError(f"missing required environment variable {name}")
    return value


def main(argv: list[str] | None = None) -> int:
    del argv
    logging.basicConfig(level=os.environ.get("TELEMETRY_LOG_LEVEL", "INFO"), format="%(message)s")
    bind_mode = _env("BIND_MODE", "5g").lower()
    device_map = _env("DEVICE_MAP_PATH", "config/devices.yaml")
    host = _env("MQTT_HOST", "127.0.0.1")
    port = int(_env("MQTT_PORT", os.environ.get("MQTT_HOST_PORT", "18830")))
    username = _env("MQTT_USERNAME")
    password = _env("MQTT_PASSWORD")
    keepalive = int(_env("MQTT_KEEPALIVE", "120"))
    qos = int(_env("MQTT_QOS", "1"))
    interval = float(_env("PUBLISH_INTERVAL_SECONDS", "2.0"))
    radio_path = _env("RADIO_MODEL_PATH", "config/radio_model.yaml")
    count_raw = os.environ.get("DEVICE_COUNT", "").strip()
    fleet_count = int(count_raw) if count_raw else None
    radio_cfg = load_radio_config(radio_path)
    if os.environ.get("ENABLE_NTN_MODEL", "").lower() in ("1", "true", "yes"):
        radio_cfg["enable_ntn"] = True
    if os.environ.get("ENABLE_A2G_MODEL", "").lower() in ("1", "true", "yes"):
        radio_cfg["enable_a2g"] = True
    radio_model = build_radio_model(radio_cfg)
    _json_log(
        logging.INFO,
        "radio_model_loaded",
        model=getattr(radio_model, "name", "unknown"),
        schema_version=SCHEMA_VERSION,
        disclaimer="modeled RF is not radio-measured",
    )

    devices = load_device_map(device_map, bind_mode, count=fleet_count)
    for device in devices:
        probe_bind(device, bind_mode)

    publishers = [
        DevicePublisher(
            device,
            bind_mode=bind_mode,
            host=host,
            port=port,
            username=username,
            password=password,
            keepalive=keepalive,
            qos=qos,
            interval=interval,
            rng=random.Random(device.device_id),
            radio_cfg=radio_cfg,
            radio_model=radio_model,
        )
        for device in devices
    ]

    stop = threading.Event()

    def _handle_stop(signum: int, _frame: object) -> None:
        _json_log(logging.INFO, "signal_received", signal=signum)
        stop.set()

    signal.signal(signal.SIGINT, _handle_stop)
    signal.signal(signal.SIGTERM, _handle_stop)

    for pub in publishers:
        pub.start()
        _json_log(
            logging.INFO,
            "simulator_started",
            devices=len(publishers),
            bind_mode=bind_mode,
        )
    while not stop.is_set():
        stop.wait(0.5)
    for pub in publishers:
        pub.stop()
    _json_log(logging.INFO, "simulator_stopped")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BindError as exc:
        LOG.error(json.dumps({"msg": "fatal_bind_error", "error": str(exc)}))
        sys.exit(2)
