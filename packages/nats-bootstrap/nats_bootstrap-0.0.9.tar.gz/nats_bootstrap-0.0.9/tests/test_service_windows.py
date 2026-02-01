from __future__ import annotations

from pathlib import Path

from nats_bootstrap import service_windows as svc


def test_build_service_binpath_without_config():
    binary = Path(r"C:\Program Files\nats\nats-server.exe")
    result = svc.build_service_binpath(binary, None)
    assert result == "\"C:\\Program Files\\nats\\nats-server.exe\""


def test_build_service_binpath_with_config():
    binary = Path(r"C:\Program Files\nats\nats-server.exe")
    config = r"C:\nats\nats.conf"
    result = svc.build_service_binpath(binary, config)
    assert result == "\"C:\\Program Files\\nats\\nats-server.exe\" -c \"C:\\nats\\nats.conf\""


def test_parse_service_state():
    sample = (
        "SERVICE_NAME: nats-bootstrap\n"
        "        TYPE               : 10  WIN32_OWN_PROCESS\n"
        "        STATE              : 4  RUNNING\n"
    )
    assert svc.parse_service_state(sample) == "RUNNING"
