from __future__ import annotations

from typing import Protocol

from iot_schema.payload import DeviceStatusPayload, TelemetryPayload


class Storage(Protocol):
    def upsert_device(
        self, device_id: str, source_ip: str | None, bind_mode: str | None
    ) -> None: ...

    def write_telemetry_batch(self, rows: list[TelemetryPayload]) -> None: ...

    def write_status(self, status: DeviceStatusPayload) -> None: ...

    def write_dead_letter(
        self, topic: str | None, reason: str, payload: str, source: str = "mqtt"
    ) -> None: ...

    def write_echo_rtt(
        self, device_id: str, sequence_number: int | None, rtt_ms: float
    ) -> None: ...

    def upsert_flow_kpis(self, device_id: str, stats: dict) -> None: ...

    def close(self) -> None: ...
