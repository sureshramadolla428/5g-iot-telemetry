"""Environment-driven consumer settings. No machine-specific IPs hardcoded."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    mqtt_host: str = "mosquitto"
    mqtt_port: int = 1883
    mqtt_username: str = "iotuser"
    mqtt_password: str = "change-me-mqtt"
    mqtt_keepalive: int = 120
    mqtt_qos: int = 1
    consumer_client_id: str = "iot-backend-consumer"

    postgres_host: str = "timescaledb"
    postgres_port: int = 5432
    postgres_user: str = "iot"
    postgres_password: str = "change-me-postgres"
    postgres_db: str = "iot"

    consumer_bind_host: str = "0.0.0.0"
    consumer_bind_port: int = 8080

    batch_size: int = 50
    batch_flush_seconds: float = 2.0
    dead_letter_max_payload_bytes: int = 8192

    enable_kafka_bridge: bool = False
    enable_amqp_bridge: bool = False
    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_topic: str = "iot.telemetry"
    amqp_url: str = "amqp://iotuser:change-me-amqp@rabbitmq:5672/%2F"
    amqp_exchange: str = "iot"
    amqp_routing_key: str = "telemetry"

    @property
    def dsn(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


def load_settings() -> Settings:
    return Settings()
