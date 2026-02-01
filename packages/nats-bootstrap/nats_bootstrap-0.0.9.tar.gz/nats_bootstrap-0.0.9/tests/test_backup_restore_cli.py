from __future__ import annotations

import os
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


def test_backup_requires_nats_cli(tmp_path):
    env = os.environ.copy()
    env["PATH"] = ""
    result = _run(
        ["backup", "--stream", "TEST", "--output", str(tmp_path)],
        env,
    )
    assert result.returncode == 2
    assert "nats cli not found" in result.stderr


def test_restore_requires_confirm(tmp_path):
    env = os.environ.copy()
    env["PATH"] = ""
    result = _run(
        ["restore", "--input", str(tmp_path)],
        env,
    )
    assert result.returncode == 2
    assert "--confirm is required" in result.stderr
