from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


def test_doctor_outputs_priority_and_pid(tmp_path):
    config_path = tmp_path / "nats-config.json"
    config_path.write_text("{\"nats_server_path\": null}", encoding="utf-8")

    dummy = tmp_path / "nats-server.exe"
    dummy.write_text("dummy", encoding="utf-8")

    env = os.environ.copy()
    env["NATS_SERVER_PATH"] = str(dummy)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "nats_bootstrap",
            "doctor",
            "--config",
            str(config_path),
        ],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert result.returncode == 0
    stdout = result.stdout
    assert "priority:" in stdout
    assert "resolution:" in stdout
    assert "pid-file:" in stdout
    assert "nats-cli:" in stdout
    assert "env:NATS_SERVER_PATH" in stdout
