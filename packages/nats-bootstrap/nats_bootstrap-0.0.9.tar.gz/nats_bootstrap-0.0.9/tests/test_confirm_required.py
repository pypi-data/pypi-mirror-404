from __future__ import annotations

import os
import subprocess
import sys


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "nats_bootstrap"] + args,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
        check=False,
    )


def test_down_requires_confirm():
    result = _run(["down"])
    assert result.returncode == 2
    assert "--confirm is required" in result.stderr


def test_leave_requires_confirm():
    result = _run(["leave", "--controller", "http://127.0.0.1:9999"])
    assert result.returncode == 2
    assert "--confirm is required" in result.stderr
