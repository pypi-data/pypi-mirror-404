from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import importlib.util
import os
import re
import shutil
import subprocess
from typing import Mapping

from .config import BootstrapConfig, ConfigLoadResult


class BinaryNotFoundError(RuntimeError):
    def __init__(self, message: str, attempts: list[ResolveAttempt]):
        super().__init__(message)
        self.attempts = attempts


@dataclass(frozen=True)
class ResolveAttempt:
    source: str
    candidate: str | None
    ok: bool
    reason: str | None


@dataclass(frozen=True)
class ResolvedBinary:
    path: Path
    source: str
    version: str | None
    version_raw: str | None


_VERSION_RE = re.compile(r"v\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?")


def resolve_binary_with_attempts(
    cli_path: str | None,
    config_result: ConfigLoadResult,
    env: Mapping[str, str],
) -> tuple[ResolvedBinary, list[ResolveAttempt]]:
    attempts: list[ResolveAttempt] = []

    def record(source: str, candidate: str | None, ok: bool, reason: str | None) -> None:
        attempts.append(
            ResolveAttempt(
                source=source,
                candidate=candidate,
                ok=ok,
                reason=reason,
            )
        )

    def validate_candidate(source: str, candidate: str | None) -> Path | None:
        if not candidate:
            record(source, None, False, "not set")
            return None
        path = Path(candidate).expanduser()
        try:
            path = path.resolve()
        except Exception:
            path = path.absolute()
        if not path.exists():
            record(source, str(path), False, "path not found")
            return None
        if not path.is_file():
            record(source, str(path), False, "not a file")
            return None
        record(source, str(path), True, None)
        return path

    resolved = validate_candidate("cli", cli_path)
    if resolved:
        return _finalize_resolved(resolved, "cli"), attempts

    resolved = _resolve_from_config(config_result, record, validate_candidate)
    if resolved:
        return _finalize_resolved(resolved, "config"), attempts

    resolved = _resolve_from_env(env, record, validate_candidate)
    if resolved:
        return _finalize_resolved(resolved, "env"), attempts

    resolved = _resolve_from_nats_server_bin(record, validate_candidate)
    if resolved:
        return _finalize_resolved(resolved, "nats-server-bin"), attempts

    resolved = _resolve_from_path(record, validate_candidate)
    if resolved:
        return _finalize_resolved(resolved, "path"), attempts

    raise BinaryNotFoundError("nats-server not found", attempts)


def _resolve_from_config(
    config_result: ConfigLoadResult,
    record,
    validate_candidate,
) -> Path | None:
    if not config_result.exists:
        record("config", str(config_result.path), False, "config file missing")
        return None
    return validate_candidate("config", config_result.config.nats_server_path)


def _resolve_from_env(
    env: Mapping[str, str],
    record,
    validate_candidate,
) -> Path | None:
    if "NATS_SERVER_PATH" in env:
        return validate_candidate("env:NATS_SERVER_PATH", env.get("NATS_SERVER_PATH"))
    if "NATS_SERVER_BIN" in env:
        return validate_candidate("env:NATS_SERVER_BIN", env.get("NATS_SERVER_BIN"))
    record("env", None, False, "NATS_SERVER_PATH/NATS_SERVER_BIN not set")
    return None


def _resolve_from_nats_server_bin(record, validate_candidate) -> Path | None:
    candidate, reason = _find_nats_server_bin_candidate()
    if candidate is None:
        record("nats-server-bin", None, False, reason)
        return None
    return validate_candidate("nats-server-bin", candidate)


def _resolve_from_path(record, validate_candidate) -> Path | None:
    names = ["nats-server.exe", "nats-server"] if os.name == "nt" else ["nats-server"]
    for name in names:
        found = shutil.which(name)
        if found:
            return validate_candidate("path", found)
    record("path", None, False, "not found in PATH")
    return None


def _find_nats_server_bin_candidate() -> tuple[str | None, str | None]:
    spec = importlib.util.find_spec("nats_server_bin")
    if spec is None or spec.origin is None:
        return None, "module not installed"
    module_path = Path(spec.origin)
    module_dir = module_path.parent

    if not module_dir.exists():
        return None, "module path missing"

    candidates = list(module_dir.rglob("nats-server*"))
    if not candidates:
        return None, "binary not found in package"

    preferred = None
    if os.name == "nt":
        for cand in candidates:
            if cand.name.lower() == "nats-server.exe":
                preferred = cand
                break
    if preferred is None:
        for cand in candidates:
            if cand.name == "nats-server":
                preferred = cand
                break

    chosen = preferred or candidates[0]
    return str(chosen), None


def _finalize_resolved(path: Path, source: str) -> ResolvedBinary:
    version, raw = _read_nats_server_version(path)
    return ResolvedBinary(path=path, source=source, version=version, version_raw=raw)


def _read_nats_server_version(path: Path) -> tuple[str | None, str | None]:
    try:
        result = subprocess.run(
            [str(path), "-v"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except Exception:
        return None, None

    output = (result.stdout or "") + (result.stderr or "")
    output = output.strip() if output else None
    if not output:
        return None, None

    match = _VERSION_RE.search(output)
    if match:
        return match.group(0), output
    return None, output
