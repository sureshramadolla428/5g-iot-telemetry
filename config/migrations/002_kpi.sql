-- Apply only if the Timescale volume already exists from v1 (schema.sql will not re-run).
-- Fresh installs already include these objects via config/schema.sql.
--   docker compose -p 5g-iot-telemetry exec -T timescaledb \
--     psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < config/migrations/002_kpi.sql
-- Never run this against other labs' databases.

ALTER TABLE telemetry ADD COLUMN IF NOT EXISTS schema_version TEXT;
ALTER TABLE telemetry ADD COLUMN IF NOT EXISTS sequence_number BIGINT;
ALTER TABLE telemetry ADD COLUMN IF NOT EXISTS radio_source TEXT;
ALTER TABLE telemetry ADD COLUMN IF NOT EXISTS radio_disclaimer TEXT;
ALTER TABLE telemetry ADD COLUMN IF NOT EXISTS rsrp_dbm DOUBLE PRECISION;
ALTER TABLE telemetry ADD COLUMN IF NOT EXISTS rsrp_mw DOUBLE PRECISION;
ALTER TABLE telemetry ADD COLUMN IF NOT EXISTS rssi_dbm DOUBLE PRECISION;
ALTER TABLE telemetry ADD COLUMN IF NOT EXISTS rssi_mw DOUBLE PRECISION;
ALTER TABLE telemetry ADD COLUMN IF NOT EXISTS rsrq_db DOUBLE PRECISION;
ALTER TABLE telemetry ADD COLUMN IF NOT EXISTS sinr_db DOUBLE PRECISION;
ALTER TABLE telemetry ADD COLUMN IF NOT EXISTS snr_db DOUBLE PRECISION;
ALTER TABLE telemetry ADD COLUMN IF NOT EXISTS cqi INTEGER;
ALTER TABLE telemetry ADD COLUMN IF NOT EXISTS mcs INTEGER;
ALTER TABLE telemetry ADD COLUMN IF NOT EXISTS tbs_bits INTEGER;
ALTER TABLE telemetry ADD COLUMN IF NOT EXISTS path_loss_db DOUBLE PRECISION;
ALTER TABLE telemetry ADD COLUMN IF NOT EXISTS p_rx_dbm DOUBLE PRECISION;
ALTER TABLE telemetry ADD COLUMN IF NOT EXISTS doppler_hz DOUBLE PRECISION;
ALTER TABLE telemetry ADD COLUMN IF NOT EXISTS l_up_ms DOUBLE PRECISION;
ALTER TABLE telemetry ADD COLUMN IF NOT EXISTS latency_budget_pct DOUBLE PRECISION;
ALTER TABLE telemetry ADD COLUMN IF NOT EXISTS rtt_ms DOUBLE PRECISION;
ALTER TABLE telemetry ADD COLUMN IF NOT EXISTS owd_ms DOUBLE PRECISION;
ALTER TABLE telemetry ADD COLUMN IF NOT EXISTS jitter_rfc3550_ms DOUBLE PRECISION;
ALTER TABLE telemetry ADD COLUMN IF NOT EXISTS iface_rx_bytes BIGINT;
ALTER TABLE telemetry ADD COLUMN IF NOT EXISTS iface_tx_bytes BIGINT;
ALTER TABLE telemetry ADD COLUMN IF NOT EXISTS ingest_lag_ms DOUBLE PRECISION;

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
