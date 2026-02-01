from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


class ConfigError(ValueError):
    pass


ALLOWED_KEYS = {"nats_server_path"}


@dataclass(frozen=True)
class BootstrapConfig:
    nats_server_path: str | None = None


@dataclass(frozen=True)
class ConfigLoadResult:
    path: Path
    exists: bool
    config: BootstrapConfig


def default_config_path() -> Path:
    cwd_path = Path.cwd() / "nats-config.json"
    if cwd_path.exists():
        return cwd_path
    return Path.home() / ".nats-bootstrap" / "nats-config.json"


def load_config(path: Path) -> ConfigLoadResult:
    if not path.exists():
        return ConfigLoadResult(path=path, exists=False, config=BootstrapConfig())

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ConfigError("config is not valid JSON") from exc

    if not isinstance(data, dict):
        raise ConfigError("config must be a JSON object")

    unknown_keys = set(data) - ALLOWED_KEYS
    if unknown_keys:
        unknown_list = ", ".join(sorted(unknown_keys))
        raise ConfigError(f"unknown config keys: {unknown_list}")

    nats_server_path = data.get("nats_server_path")
    if nats_server_path is not None and not isinstance(nats_server_path, str):
        raise ConfigError("nats_server_path must be a string")

    return ConfigLoadResult(
        path=path,
        exists=True,
        config=BootstrapConfig(nats_server_path=nats_server_path),
    )
