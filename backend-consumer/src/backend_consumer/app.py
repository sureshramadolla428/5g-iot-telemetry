from __future__ import annotations

from fastapi import FastAPI

from backend_consumer.models.counters import Counters
from backend_consumer.storage.base import Storage


def create_app(counters: Counters, storage: Storage) -> FastAPI:
    app = FastAPI(title="5G IoT telemetry consumer", version="1.0.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready")
    def ready() -> dict[str, object]:
        db_ok = False
        try:
            db_ok = storage.ping()
        except Exception:
            db_ok = False
        snap = counters.snapshot()
        ready_flag = db_ok and bool(snap["mqtt_connected"])
        return {"ready": ready_flag, "db": db_ok, "counters": snap}

    @app.get("/metrics")
    def metrics() -> dict[str, object]:
        return counters.snapshot()

    return app
