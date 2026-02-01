from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import socket


DEFAULT_DATA_DIRNAME = "nats-bootstrap-data"
DEFAULT_CONFIG_NAME = "nats-bootstrap.conf"
DEFAULT_CLIENT_PORT = 4222
DEFAULT_HTTP_PORT = 8222
DEFAULT_CLUSTER_PORT = 6222
DEFAULT_CLUSTER_LISTEN = "0.0.0.0"


class BootstrapConfigError(ValueError):
    pass


@dataclass(frozen=True)
class GeneratedConfig:
    path: Path
    data_dir: Path


def default_data_dir() -> Path:
    return (Path.cwd() / DEFAULT_DATA_DIRNAME).resolve()


def resolve_data_dir(value: str | None) -> Path:
    if value:
        return Path(value).expanduser().resolve()
    return default_data_dir()


def config_path_for_data_dir(data_dir: Path) -> Path:
    return data_dir / DEFAULT_CONFIG_NAME


def normalize_seed(seed: str, default_port: int = DEFAULT_CLUSTER_PORT) -> str:
    raw = seed.strip()
    if "://" in raw:
        return raw
    if ":" in raw:
        return f"nats://{raw}"
    return f"nats://{raw}:{default_port}"


def resolve_cluster_listen(listen: str | None, cluster_port: int) -> str:
    value = listen.strip() if listen else DEFAULT_CLUSTER_LISTEN
    if ":" in value:
        return value
    return f"{value}:{cluster_port}"


def generate_bootstrap_config(
    cluster: str,
    data_dir: Path,
    seed: str | None,
    server_name: str | None = None,
    client_port: int = DEFAULT_CLIENT_PORT,
    http_port: int = DEFAULT_HTTP_PORT,
    cluster_port: int = DEFAULT_CLUSTER_PORT,
    cluster_listen: str | None = None,
) -> GeneratedConfig:
    cluster_name = cluster.strip()
    if not cluster_name:
        raise BootstrapConfigError("cluster name is required")

    if data_dir.exists() and not data_dir.is_dir():
        raise BootstrapConfigError("data folder is not a directory")

    data_dir.mkdir(parents=True, exist_ok=True)
    server_name = server_name or socket.gethostname()

    config_path = config_path_for_data_dir(data_dir)
    text = _build_config_text(
        cluster_name,
        data_dir,
        seed,
        server_name,
        client_port,
        http_port,
        cluster_port,
        cluster_listen,
    )
    config_path.write_text(text, encoding="utf-8")
    return GeneratedConfig(path=config_path, data_dir=data_dir)


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _build_config_text(
    cluster: str,
    data_dir: Path,
    seed: str | None,
    server_name: str,
    client_port: int,
    http_port: int,
    cluster_port: int,
    cluster_listen: str | None,
) -> str:
    store_dir = _escape(str(data_dir))
    cluster_name = _escape(cluster)
    server_name = _escape(server_name)

    listen_value = resolve_cluster_listen(cluster_listen, cluster_port)
    lines = [
        f'server_name: "{server_name}"',
        f"port: {client_port}",
        f"http: {http_port}",
        f'jetstream: {{ store_dir: "{store_dir}" }}',
        "",
        "cluster {",
        f'  name: "{cluster_name}"',
        f'  listen: "{listen_value}"',
    ]

    if seed:
        seed_value = _escape(normalize_seed(seed, cluster_port))
        lines += [
            "  routes = [",
            f'    "{seed_value}"',
            "  ]",
        ]

    lines.append("}")
    lines.append("")
    return "\n".join(lines)
