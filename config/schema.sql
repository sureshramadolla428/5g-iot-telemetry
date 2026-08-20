-- Shared TimescaleDB schema for 5G IoT telemetry (single source of truth).
-- Applied once via /docker-entrypoint-initdb.d on first volume init.
-- RF columns are MODELED (source=modeled). Never AVG(rsrp_dbm) — use rsrp_mw.

CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS devices (
    device_id   TEXT PRIMARY KEY,
    first_seen  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_status TEXT NOT NULL DEFAULT 'unknown',
    source_ip   TEXT,
    bind_mode   TEXT
);

CREATE TABLE IF NOT EXISTS telemetry (
    timestamp   TIMESTAMPTZ NOT NULL,
    device_id   TEXT NOT NULL REFERENCES devices (device_id),
    temperature DOUBLE PRECISION NOT NULL,
    humidity    DOUBLE PRECISION NOT NULL,
    battery     DOUBLE PRECISION NOT NULL,
    latitude    DOUBLE PRECISION NOT NULL,
    longitude   DOUBLE PRECISION NOT NULL,
    status      TEXT NOT NULL,
    source_ip   TEXT,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    schema_version TEXT,
    sequence_number BIGINT,
    radio_source TEXT,
    radio_disclaimer TEXT,
    rsrp_dbm    DOUBLE PRECISION,
    rsrp_mw     DOUBLE PRECISION,
    rssi_dbm    DOUBLE PRECISION,
    rssi_mw     DOUBLE PRECISION,
    rsrq_db     DOUBLE PRECISION,
    sinr_db     DOUBLE PRECISION,
    snr_db      DOUBLE PRECISION,
    cqi         INTEGER,
    mcs         INTEGER,
    tbs_bits    INTEGER,
    path_loss_db DOUBLE PRECISION,
    p_rx_dbm    DOUBLE PRECISION,
    doppler_hz  DOUBLE PRECISION,
    l_up_ms     DOUBLE PRECISION,
    latency_budget_pct DOUBLE PRECISION,
    rtt_ms      DOUBLE PRECISION,
    owd_ms      DOUBLE PRECISION,
    jitter_rfc3550_ms DOUBLE PRECISION,
    iface_rx_bytes BIGINT,
    iface_tx_bytes BIGINT,
    ingest_lag_ms DOUBLE PRECISION
);

COMMENT ON COLUMN telemetry.rsrp_dbm IS
    'MODELED dBm. FORBIDDEN: AVG(rsrp_dbm). Use dbm_from_mw(AVG(rsrp_mw)).';
COMMENT ON COLUMN telemetry.rsrp_mw IS
    'Linear RSRP in mW for correct power averaging.';
COMMENT ON COLUMN telemetry.radio_source IS
    'Must be modeled for PHY fields. UERANSIM has no radio measurements.';

SELECT create_hypertable(
    'telemetry',
    'timestamp',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS telemetry_device_time_idx
    ON telemetry (device_id, timestamp DESC);

ALTER TABLE telemetry SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'device_id',
    timescaledb.compress_orderby = 'timestamp DESC'
);

SELECT add_compression_policy('telemetry', INTERVAL '7 days', if_not_exists => TRUE);
SELECT add_retention_policy('telemetry', INTERVAL '30 days', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS dead_letter (
    id          BIGSERIAL PRIMARY KEY,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    topic       TEXT,
    reason      TEXT NOT NULL,
    payload     TEXT,
    source      TEXT
);

CREATE INDEX IF NOT EXISTS dead_letter_received_idx
    ON dead_letter (received_at DESC);

CREATE TABLE IF NOT EXISTS device_status (
    timestamp   TIMESTAMPTZ NOT NULL,
    device_id   TEXT NOT NULL REFERENCES devices (device_id),
    status      TEXT NOT NULL,
    detail      TEXT,
    PRIMARY KEY (device_id, timestamp)
);

SELECT create_hypertable(
    'device_status',
    'timestamp',
    if_not_exists => TRUE
);

CREATE TABLE IF NOT EXISTS echo_rtt (
    timestamp   TIMESTAMPTZ NOT NULL,
    device_id   TEXT NOT NULL,
    sequence_number BIGINT,
    rtt_ms      DOUBLE PRECISION NOT NULL
);

SELECT create_hypertable('echo_rtt', 'timestamp', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS device_flow_kpis (
    device_id     TEXT PRIMARY KEY REFERENCES devices (device_id),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    received      BIGINT NOT NULL DEFAULT 0,
    duplicates    BIGINT NOT NULL DEFAULT 0,
    gaps          BIGINT NOT NULL DEFAULT 0,
    reorders      BIGINT NOT NULL DEFAULT 0,
    pdr           DOUBLE PRECISION,
    plr           DOUBLE PRECISION,
    msg_rate_hz   DOUBLE PRECISION,
    last_seq      BIGINT
);

CREATE OR REPLACE FUNCTION dbm_from_mw(mw DOUBLE PRECISION)
RETURNS DOUBLE PRECISION
LANGUAGE sql
IMMUTABLE
AS $$
    SELECT CASE
        WHEN mw IS NULL OR mw <= 0 THEN NULL
        ELSE 10.0 * log(10, mw)
    END
$$;

CREATE OR REPLACE FUNCTION mw_from_dbm(dbm DOUBLE PRECISION)
RETURNS DOUBLE PRECISION
LANGUAGE sql
IMMUTABLE
AS $$
    SELECT CASE
        WHEN dbm IS NULL THEN NULL
        ELSE power(10.0, dbm / 10.0)
    END
$$;

-- Correct RSRP average: linear power then back to dBm. Mirrors metrics.avg_db().
CREATE OR REPLACE VIEW v_rsrp_avg AS
SELECT
    device_id,
    dbm_from_mw(AVG(rsrp_mw)) AS rsrp_dbm_avg_power,
    AVG(rsrp_mw) AS rsrp_mw_avg,
    COUNT(*) AS n
FROM telemetry
WHERE rsrp_mw IS NOT NULL
GROUP BY device_id;

CREATE OR REPLACE VIEW v_kpi_modeled AS
SELECT
    timestamp,
    device_id,
    radio_source,
    radio_disclaimer,
    rsrp_dbm,
    rsrp_mw,
    rsrq_db,
    sinr_db,
    cqi,
    mcs,
    tbs_bits,
    path_loss_db,
    doppler_hz,
    l_up_ms,
    latency_budget_pct
FROM telemetry
WHERE radio_source = 'modeled';

CREATE OR REPLACE VIEW v_kpi_measured AS
SELECT
    timestamp,
    device_id,
    sequence_number,
    rtt_ms,
    owd_ms,
    jitter_rfc3550_ms,
    iface_rx_bytes,
    iface_tx_bytes,
    ingest_lag_ms
FROM telemetry;
