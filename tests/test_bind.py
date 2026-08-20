from __future__ import annotations

import socket
from unittest.mock import MagicMock

import pytest

from iot_schema.bind import BindError, create_source_bound_socket, require_explicit_source_ip


def test_5g_requires_explicit_ip():
    with pytest.raises(BindError, match="auto-select"):
        require_explicit_source_ip(None, bind_mode="5g", device_id="iot-001", interface="uesimtun0")
    with pytest.raises(BindError, match="auto-select"):
        require_explicit_source_ip("auto", bind_mode="5g", device_id="iot-001")
    with pytest.raises(BindError, match="auto-select"):
        require_explicit_source_ip("first", bind_mode="5g", device_id="iot-001")


def test_5g_accepts_explicit_ipv4():
    ip = require_explicit_source_ip("10.45.0.2", bind_mode="5g", device_id="iot-001")
    assert ip == "10.45.0.2"


def test_direct_does_not_bind():
    assert require_explicit_source_ip("10.45.0.2", bind_mode="direct", device_id="iot-001") is None


def test_unknown_bind_mode_rejected():
    with pytest.raises(BindError, match="BIND_MODE"):
        require_explicit_source_ip("10.45.0.2", bind_mode="host", device_id="iot-001")


def test_create_socket_binds_in_5g_mode():
    fake = MagicMock()

    def factory(*_args, **_kwargs):
        return fake

    sock = create_source_bound_socket(
        "10.45.0.2",
        bind_mode="5g",
        device_id="iot-001",
        interface="uesimtun0",
        sock_cls=factory,
    )
    assert sock is fake
    fake.bind.assert_called_once_with(("10.45.0.2", 0))


def test_create_socket_skips_bind_in_direct_mode():
    fake = MagicMock()

    def factory(*_args, **_kwargs):
        return fake

    create_source_bound_socket(
        "10.45.0.2",
        bind_mode="direct",
        device_id="iot-001",
        sock_cls=factory,
    )
    fake.bind.assert_not_called()


def test_bind_failure_is_loud():
    fake = MagicMock()
    fake.bind.side_effect = OSError("Cannot assign requested address")

    def factory(*_args, **_kwargs):
        return fake

    with pytest.raises(BindError, match="failed to bind"):
        create_source_bound_socket(
            "10.45.0.2",
            bind_mode="5g",
            device_id="iot-001",
            interface="uesimtun0",
            sock_cls=factory,
        )
    fake.close.assert_called()


def test_never_invents_uesimtun_from_socket_list(monkeypatch):
    monkeypatch.setattr(socket, "if_nameindex", lambda: [(1, "uesimtun0"), (2, "uesimtun1")])
    with pytest.raises(BindError, match="auto-select"):
        require_explicit_source_ip("", bind_mode="5g", device_id="iot-001")
