from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import shutil
from typing import Mapping


@dataclass(frozen=True)
class ResolvedNatsCli:
    path: Path
    source: str


class NatsCliNotFoundError(RuntimeError):
    pass


def resolve_nats_cli(cli_path: str | None, env: Mapping[str, str]) -> ResolvedNatsCli:
    if cli_path:
        path = _validate(Path(cli_path), "cli")
        if path:
            return ResolvedNatsCli(path=path, source="cli")

    env_path = env.get("NATS_CLI_PATH")
    if env_path:
        path = _validate(Path(env_path), "env")
        if path:
            return ResolvedNatsCli(path=path, source="env")

    found = shutil.which("nats")
    if found:
        path = _validate(Path(found), "path")
        if path:
            return ResolvedNatsCli(path=path, source="path")

    raise NatsCliNotFoundError("nats cli not found")


def _validate(path: Path, source: str) -> Path | None:
    try:
        resolved = path.expanduser().resolve()
    except Exception:
        resolved = path.absolute()
    if not resolved.exists():
        return None
    if not resolved.is_file():
        return None
    return resolved
