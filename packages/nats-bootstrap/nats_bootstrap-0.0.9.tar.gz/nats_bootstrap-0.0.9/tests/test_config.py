from __future__ import annotations

from pathlib import Path

import pytest

from nats_bootstrap.config import ConfigError, load_config


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_config_rejects_unknown_keys(tmp_path):
    path = _write(tmp_path / "nats-config.json", "{\"unknown\": 1}")
    with pytest.raises(ConfigError):
        load_config(path)


def test_config_rejects_non_object(tmp_path):
    path = _write(tmp_path / "nats-config.json", "[1,2,3]")
    with pytest.raises(ConfigError):
        load_config(path)


def test_config_rejects_invalid_json(tmp_path):
    path = _write(tmp_path / "nats-config.json", "{invalid}")
    with pytest.raises(ConfigError):
        load_config(path)


def test_config_rejects_non_string_path(tmp_path):
    path = _write(tmp_path / "nats-config.json", "{\"nats_server_path\": 123}")
    with pytest.raises(ConfigError):
        load_config(path)


def test_config_accepts_valid(tmp_path):
    path = _write(tmp_path / "nats-config.json", "{\"nats_server_path\": \"C:/bin/nats-server.exe\"}")
    result = load_config(path)
    assert result.config.nats_server_path == "C:/bin/nats-server.exe"
