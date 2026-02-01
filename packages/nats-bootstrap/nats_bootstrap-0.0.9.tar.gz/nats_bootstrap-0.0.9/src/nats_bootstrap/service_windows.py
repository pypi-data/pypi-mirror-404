from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import shutil
import subprocess


DEFAULT_SERVICE_NAME = "nats-bootstrap"
DEFAULT_BIN_DIR = Path(r"C:\ProgramData\nats-bootstrap\bin")


@dataclass(frozen=True)
class ServiceInstallSpec:
    service_name: str
    bin_dir: Path | None
    nats_config: str | None


def is_windows() -> bool:
    return os.name == "nt"


def build_service_binpath(binary: Path, nats_config: str | None) -> str:
    cmd = [f"\"{binary}\""]
    if nats_config:
        cmd.append(f"-c \"{nats_config}\"")
    return " ".join(cmd)


def sc_query_args(service_name: str) -> list[str]:
    return ["sc", "query", service_name]


def sc_create_args(service_name: str, bin_path: str) -> list[str]:
    return ["sc", "create", service_name, "binPath=", bin_path, "start=", "demand"]


def sc_delete_args(service_name: str) -> list[str]:
    return ["sc", "delete", service_name]


def sc_stop_args(service_name: str) -> list[str]:
    return ["sc", "stop", service_name]


def sc_start_args(service_name: str) -> list[str]:
    return ["sc", "start", service_name]


def sc_run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, check=False)


def ensure_binary(spec: ServiceInstallSpec, source_binary: Path) -> Path:
    if spec.bin_dir is None:
        return source_binary
    spec.bin_dir.mkdir(parents=True, exist_ok=True)
    target = spec.bin_dir / "nats-server.exe"
    shutil.copy2(source_binary, target)
    return target


def service_exists(service_name: str) -> bool:
    result = sc_run(sc_query_args(service_name))
    return result.returncode == 0


def install_service(spec: ServiceInstallSpec, source_binary: Path) -> subprocess.CompletedProcess[str]:
    binary = ensure_binary(spec, source_binary)
    bin_path = build_service_binpath(binary, spec.nats_config)
    return sc_run(sc_create_args(spec.service_name, bin_path))


def uninstall_service(service_name: str) -> subprocess.CompletedProcess[str]:
    sc_run(sc_stop_args(service_name))
    return sc_run(sc_delete_args(service_name))


def start_service(service_name: str) -> subprocess.CompletedProcess[str]:
    return sc_run(sc_start_args(service_name))


def query_service(service_name: str) -> subprocess.CompletedProcess[str]:
    return sc_run(sc_query_args(service_name))


def parse_service_state(output: str) -> str | None:
    for line in output.splitlines():
        if "STATE" in line:
            parts = line.split()
            if parts:
                return parts[-1]
    return None
