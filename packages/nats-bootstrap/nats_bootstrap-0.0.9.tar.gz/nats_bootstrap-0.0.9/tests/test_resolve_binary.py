from __future__ import annotations

from pathlib import Path

import nats_bootstrap.resolve as resolve
from nats_bootstrap.config import BootstrapConfig, ConfigLoadResult


def _touch(path: Path) -> Path:
    path.write_text("dummy", encoding="utf-8")
    return path


def _config(path: Path, nats_server_path: str | None, exists: bool) -> ConfigLoadResult:
    return ConfigLoadResult(
        path=path,
        exists=exists,
        config=BootstrapConfig(nats_server_path=nats_server_path),
    )


def test_resolve_prefers_cli_over_others(tmp_path, monkeypatch):
    cli = _touch(tmp_path / "cli.exe")
    config_path = tmp_path / "nats-config.json"
    config = _config(config_path, str(_touch(tmp_path / "config.exe")), True)
    env = {"NATS_SERVER_PATH": str(_touch(tmp_path / "env.exe"))}

    monkeypatch.setattr(resolve, "_read_nats_server_version", lambda _: (None, None))

    resolved, _ = resolve.resolve_binary_with_attempts(str(cli), config, env)
    assert resolved.path == cli.resolve()
    assert resolved.source == "cli"


def test_resolve_prefers_config_over_env(tmp_path, monkeypatch):
    config_path = tmp_path / "nats-config.json"
    config = _config(config_path, str(_touch(tmp_path / "config.exe")), True)
    env = {"NATS_SERVER_PATH": str(_touch(tmp_path / "env.exe"))}

    monkeypatch.setattr(resolve, "_read_nats_server_version", lambda _: (None, None))

    resolved, _ = resolve.resolve_binary_with_attempts(None, config, env)
    assert resolved.path == Path(config.config.nats_server_path).resolve()
    assert resolved.source == "config"


def test_resolve_prefers_env_when_config_missing(tmp_path, monkeypatch):
    config_path = tmp_path / "nats-config.json"
    config = _config(config_path, None, False)
    env = {"NATS_SERVER_PATH": str(_touch(tmp_path / "env.exe"))}

    monkeypatch.setattr(resolve, "_read_nats_server_version", lambda _: (None, None))

    resolved, _ = resolve.resolve_binary_with_attempts(None, config, env)
    assert resolved.path == Path(env["NATS_SERVER_PATH"]).resolve()
    assert resolved.source == "env"


def test_resolve_prefers_nats_server_bin_over_path(tmp_path, monkeypatch):
    config_path = tmp_path / "nats-config.json"
    config = _config(config_path, None, False)
    env = {}

    bin_path = _touch(tmp_path / "bin.exe")
    monkeypatch.setattr(resolve, "_find_nats_server_bin_candidate", lambda: (str(bin_path), None))
    monkeypatch.setattr(resolve, "_read_nats_server_version", lambda _: (None, None))

    resolved, _ = resolve.resolve_binary_with_attempts(None, config, env)
    assert resolved.path == bin_path.resolve()
    assert resolved.source == "nats-server-bin"


def test_resolve_falls_back_to_path(tmp_path, monkeypatch):
    config_path = tmp_path / "nats-config.json"
    config = _config(config_path, None, False)
    env = {}

    path_bin = _touch(tmp_path / "path.exe")
    monkeypatch.setattr(resolve, "_find_nats_server_bin_candidate", lambda: (None, "module not installed"))
    monkeypatch.setattr(resolve.shutil, "which", lambda _: str(path_bin))
    monkeypatch.setattr(resolve, "_read_nats_server_version", lambda _: (None, None))

    resolved, _ = resolve.resolve_binary_with_attempts(None, config, env)
    assert resolved.path == path_bin.resolve()
    assert resolved.source == "path"
