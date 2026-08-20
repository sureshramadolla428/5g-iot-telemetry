# Tests for payload validation, telemetry bounds, topics, and source-IP bind policy.
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "config" / "payload.schema.json"


@pytest.fixture(scope="session")
def payload_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
