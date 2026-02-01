from __future__ import annotations

from pathlib import Path

import pytest

from nats_bootstrap.nats_cli import NatsCliNotFoundError, resolve_nats_cli


def test_resolve_cli_prefers_cli_arg(tmp_path):
    cli = tmp_path / "nats"
    cli.write_text("dummy", encoding="utf-8")
    resolved = resolve_nats_cli(str(cli), {})
    assert resolved.path == cli.resolve()
    assert resolved.source == "cli"


def test_resolve_cli_uses_env(tmp_path):
    cli = tmp_path / "nats"
    cli.write_text("dummy", encoding="utf-8")
    resolved = resolve_nats_cli(None, {"NATS_CLI_PATH": str(cli)})
    assert resolved.path == cli.resolve()
    assert resolved.source == "env"


def test_resolve_cli_not_found():
    with pytest.raises(NatsCliNotFoundError):
        resolve_nats_cli(None, {})
