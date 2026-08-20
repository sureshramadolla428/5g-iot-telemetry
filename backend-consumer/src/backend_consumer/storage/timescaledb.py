from __future__ import annotations

import logging

import psycopg
from psycopg.rows import dict_row

from backend_consumer.storage.base import Storage
from iot_schema.payload import DeviceStatusPayload, TelemetryPayload
from iot_schema.rows import telemetry_sql_tuple

LOG = logging.getLogger("backend_consumer.storage")


class TimescaleStorage:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._conn = psycopg.connect(dsn, row_factory=dict_row, autocommit=False)

    def _commit(self) -> None:
        try:
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    def ping(self) -> bool:
        try:
            with self._conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
            self._commit()
            return True
        except Exception:
            self._conn.rollback()
            raise

    def upsert_device(self, device_id: str, source_ip: str | None, bind_mode: str | None) -> None:
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO devices (device_id, last_seen, source_ip, bind_mode)
                    VALUES (%s, NOW(), %s, %s)
                    ON CONFLICT (device_id) DO UPDATE SET
                        last_seen = NOW(),
                        source_ip = COALESCE(EXCLUDED.source_ip, devices.source_ip),
                        bind_mode = COALESCE(EXCLUDED.bind_mode, devices.bind_mode)
                    """,
                    (device_id, source_ip, bind_mode),
                )
            self._commit()
        except Exception:
            self._conn.rollback()
            raise

    def write_telemetry_batch(self, rows: list[TelemetryPayload]) -> None:
        if not rows:
            return
        try:
            with self._conn.cursor() as cur:
                for row in rows:
                    cur.execute(
                        """
                        INSERT INTO devices (device_id, last_seen, last_status, source_ip)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (device_id) DO UPDATE SET
                            last_seen = EXCLUDED.last_seen,
                            last_status = EXCLUDED.last_status,
                            source_ip = COALESCE(EXCLUDED.source_ip, devices.source_ip)
                        """,
                        (row.device_id, row.timestamp, row.status, row.source_ip),
                    )
                cur.executemany(
                    """
                    INSERT INTO telemetry (
                        timestamp, device_id, temperature, humidity, battery,
                        latitude, longitude, status, source_ip, ingested_at,
                        schema_version, sequence_number, radio_source, radio_disclaimer,
                        rsrp_dbm, rsrp_mw, rssi_dbm, rssi_mw, rsrq_db, sinr_db, snr_db,
                        cqi, mcs, tbs_bits, path_loss_db, p_rx_dbm, doppler_hz,
                        l_up_ms, latency_budget_pct, rtt_ms, owd_ms, jitter_rfc3550_ms,
                        iface_rx_bytes, iface_tx_bytes, ingest_lag_ms
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s
                    )
                    """,
                    [telemetry_sql_tuple(row) for row in rows],
                )
            self._commit()
        except Exception:
            self._conn.rollback()
            LOG.exception("telemetry batch failed")
            raise

    def write_status(self, status: DeviceStatusPayload) -> None:
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO devices (device_id, last_seen, last_status)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (device_id) DO UPDATE SET
                        last_seen = EXCLUDED.last_seen,
                        last_status = EXCLUDED.last_status
                    """,
                    (status.device_id, status.timestamp, status.status),
                )
                cur.execute(
                    """
                    INSERT INTO device_status (timestamp, device_id, status, detail)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (status.timestamp, status.device_id, status.status, status.detail),
                )
            self._commit()
        except Exception:
            self._conn.rollback()
            raise

    def write_dead_letter(
        self, topic: str | None, reason: str, payload: str, source: str = "mqtt"
    ) -> None:
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO dead_letter (topic, reason, payload, source)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (topic, reason, payload, source),
                )
            self._commit()
        except Exception:
            self._conn.rollback()
            raise

    def write_echo_rtt(
        self, device_id: str, sequence_number: int | None, rtt_ms: float
    ) -> None:
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO echo_rtt (timestamp, device_id, sequence_number, rtt_ms)
                    VALUES (NOW(), %s, %s, %s)
                    """,
                    (device_id, sequence_number, rtt_ms),
                )
            self._commit()
        except Exception:
            self._conn.rollback()
            raise

    def upsert_flow_kpis(self, device_id: str, stats: dict) -> None:
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO devices (device_id, last_seen)
                    VALUES (%s, NOW())
                    ON CONFLICT (device_id) DO UPDATE SET last_seen = NOW()
                    """,
                    (device_id,),
                )
                cur.execute(
                    """
                    INSERT INTO device_flow_kpis (
                        device_id, updated_at, received, duplicates, gaps, reorders,
                        pdr, plr, msg_rate_hz, last_seq
                    ) VALUES (%s, NOW(), %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (device_id) DO UPDATE SET
                        updated_at = NOW(),
                        received = EXCLUDED.received,
                        duplicates = EXCLUDED.duplicates,
                        gaps = EXCLUDED.gaps,
                        reorders = EXCLUDED.reorders,
                        pdr = EXCLUDED.pdr,
                        plr = EXCLUDED.plr,
                        msg_rate_hz = EXCLUDED.msg_rate_hz,
                        last_seq = EXCLUDED.last_seq
                    """,
                    (
                        device_id,
                        stats.get("received", 0),
                        stats.get("duplicates", 0),
                        stats.get("gaps", 0),
                        stats.get("reorders", 0),
                        stats.get("pdr"),
                        stats.get("plr"),
                        stats.get("msg_rate_hz"),
                        stats.get("last_seq"),
                    ),
                )
            self._commit()
        except Exception:
            self._conn.rollback()
            raise

    def close(self) -> None:
        self._conn.close()


def create_storage(dsn: str) -> Storage:
    return TimescaleStorage(dsn)
