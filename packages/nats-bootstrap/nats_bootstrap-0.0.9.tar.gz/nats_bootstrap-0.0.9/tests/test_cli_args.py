from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


def _run(args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "nats_bootstrap"] + args,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_config_argument_position(tmp_path):
    config_path = tmp_path / "nats-config.json"
    config_path.write_text("{\"nats_server_path\": null}", encoding="utf-8")
    dummy = tmp_path / "nats-server.exe"
    dummy.write_text("dummy", encoding="utf-8")

    env = os.environ.copy()
    env["NATS_SERVER_PATH"] = str(dummy)

    before = _run(["--config", str(config_path), "status"], env)
    after = _run(["status", "--config", str(config_path)], env)

    assert before.returncode == 0
    assert after.returncode == 0


def test_nats_server_path_argument_position(tmp_path):
    dummy = tmp_path / "nats-server.exe"
    dummy.write_text("dummy", encoding="utf-8")

    env = os.environ.copy()

    before = _run(["--nats-server-path", str(dummy), "status"], env)
    after = _run(["status", "--nats-server-path", str(dummy)], env)

    assert before.returncode == 0
    assert after.returncode == 0
