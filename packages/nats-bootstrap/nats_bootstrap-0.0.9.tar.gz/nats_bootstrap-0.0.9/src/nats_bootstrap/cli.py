from __future__ import annotations

import argparse
import os
from pathlib import Path
import socket
import subprocess
import sys
from typing import Sequence
import uuid

from .config import ConfigError, default_config_path, load_config
from .controller import ControllerConfig, DEFAULT_LISTEN, start_controller
from .controller_client import (
    ControllerRequestError,
    ControllerUnavailableError,
    LeaveRequest,
    call_leave,
    check_health,
)
from .nats_cli import NatsCliNotFoundError, resolve_nats_cli
from .bootstrap_config import (
    BootstrapConfigError,
    DEFAULT_CLIENT_PORT,
    DEFAULT_CLUSTER_PORT,
    DEFAULT_HTTP_PORT,
    generate_bootstrap_config,
    resolve_data_dir,
)
from .resolve import BinaryNotFoundError, resolve_binary_with_attempts
from .service_windows import (
    DEFAULT_SERVICE_NAME,
    ServiceInstallSpec,
    build_service_binpath,
    install_service,
    is_windows,
    parse_service_state,
    query_service,
    service_exists,
    start_service,
    uninstall_service,
)


MSG_NOT_FOUND = "nats-server not found"
MSG_INVALID_CONFIG = "config is invalid"
MSG_NOT_IMPLEMENTED = "this command is not implemented in MVP"
MSG_CONFIRM_REQUIRED = "--confirm is required"
MSG_CTRL_UNAVAILABLE = "controller unavailable"
MSG_CTRL_INVALID = "controller request is invalid"
MSG_BKP_NOT_FOUND = "nats cli not found"
MSG_SVC_UNSUPPORTED = "service is only supported on Windows"
MSG_SVC_EXISTS = "service already exists"
MSG_SVC_NOT_FOUND = "service not found"
MSG_BOOTSTRAP_CONFLICT = "--cluster cannot be used with --nats-config"
MSG_BOOTSTRAP_SEED_REQUIRED = "--seed is required for join when --cluster is used"
MSG_BOOTSTRAP_DATAFOLDER_INVALID = "--datafolder must be a directory"
MSG_BOOTSTRAP_CLUSTER_REQUIRED = "--cluster must not be empty"


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "start":
        print("warning: 'start' is deprecated; use 'up'", file=sys.stderr)
        args.command = "up"

    if args.command in {"status", "doctor", "up", "join"}:
        return handle_with_binary(args)

    if args.command == "backup":
        return handle_backup(args)

    if args.command == "restore":
        return handle_restore(args)

    if args.command == "service":
        return handle_service(args)

    if args.command == "controller":
        return handle_controller(args)

    if args.command == "leave":
        return handle_leave(args)

    if args.command == "down":
        return handle_down(args)

    return 2


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config", help="path to nats-config.json")
    common.add_argument("--nats-server-path", help="override nats-server path")

    parser = argparse.ArgumentParser(prog="nats-bootstrap", parents=[common])
    subparsers = parser.add_subparsers(dest="command", required=True)

    up_parser = subparsers.add_parser("up", help="start nats-server", parents=[common])
    up_parser.add_argument("--service", action="store_true", help="start service")
    up_parser.add_argument(
        "--service-name",
        default=DEFAULT_SERVICE_NAME,
        help="service name",
    )
    up_parser.add_argument("--cluster", help="cluster name (bootstrap mode)")
    up_parser.add_argument("--cluster-port", type=int, help="cluster port (bootstrap mode)")
    up_parser.add_argument("--client-port", type=int, help="client port (bootstrap mode)")
    up_parser.add_argument("--http-port", type=int, help="http port (bootstrap mode)")
    up_parser.add_argument("--listen", help="cluster listen host[:port] (bootstrap mode)")
    up_parser.add_argument(
        "--datafolder",
        "--data-folder",
        dest="datafolder",
        help="data folder (bootstrap mode)",
    )
    up_parser.add_argument("--nats-config", help="path to nats-server config file")
    up_parser.add_argument("nats_args", nargs=argparse.REMAINDER)

    join_parser = subparsers.add_parser("join", help="alias of up", parents=[common])
    join_parser.add_argument("--seed", help="seed host[:port] for join (bootstrap mode)")
    join_parser.add_argument("--cluster", help="cluster name (bootstrap mode)")
    join_parser.add_argument("--cluster-port", type=int, help="cluster port (bootstrap mode)")
    join_parser.add_argument("--client-port", type=int, help="client port (bootstrap mode)")
    join_parser.add_argument("--http-port", type=int, help="http port (bootstrap mode)")
    join_parser.add_argument("--listen", help="cluster listen host[:port] (bootstrap mode)")
    join_parser.add_argument(
        "--datafolder",
        "--data-folder",
        dest="datafolder",
        help="data folder (bootstrap mode)",
    )
    join_parser.add_argument("--nats-config", help="path to nats-server config file")
    join_parser.add_argument("nats_args", nargs=argparse.REMAINDER)

    down_parser = subparsers.add_parser("down", help="stop nats-server", parents=[common])
    down_parser.add_argument("--confirm", action="store_true", help="confirm stop")

    leave_parser = subparsers.add_parser("leave", help="leave cluster and stop", parents=[common])
    leave_parser.add_argument(
        "--controller",
        action="append",
        default=[],
        help="controller endpoint (e.g. http://127.0.0.1:8222)",
    )
    leave_parser.add_argument("--request-id", help="idempotency key")
    leave_parser.add_argument("--server-name", help="server name (default: hostname)")
    leave_parser.add_argument("--nats-url", help="nats url for controller request")
    leave_parser.add_argument(
        "--stop-anyway",
        action="store_true",
        help="allow stop when controller is unavailable (MVP: no local stop)",
    )
    leave_parser.add_argument("--confirm", action="store_true", help="confirm leave/stop")

    service_parser = subparsers.add_parser("service", help="manage service", parents=[common])
    service_sub = service_parser.add_subparsers(dest="service_command", required=True)
    service_install = service_sub.add_parser("install", help="install service", parents=[common])
    service_install.add_argument(
        "--service-name",
        default=DEFAULT_SERVICE_NAME,
        help="service name",
    )
    service_install.add_argument(
        "--bin-dir",
        help="bin directory (if set, copy nats-server.exe)",
    )
    service_install.add_argument(
        "--nats-config",
        help="path to nats-server config file",
    )

    service_uninstall = service_sub.add_parser(
        "uninstall", help="uninstall service", parents=[common]
    )
    service_uninstall.add_argument(
        "--service-name",
        default=DEFAULT_SERVICE_NAME,
        help="service name",
    )

    controller_parser = subparsers.add_parser(
        "controller",
        help="controller operations",
        parents=[common],
    )
    controller_sub = controller_parser.add_subparsers(dest="controller_command", required=True)
    controller_start = controller_sub.add_parser("start", help="start controller", parents=[common])
    controller_start.add_argument("--listen", default=DEFAULT_LISTEN, help="listen host:port")
    controller_start.add_argument("--nats-url", required=True, help="nats url for peer-remove")
    controller_start.add_argument("--sys-creds", required=True, help="path to sys.creds")
    controller_start.add_argument("--state-dir", help="state directory")

    backup_parser = subparsers.add_parser("backup", help="backup JetStream", parents=[common])
    backup_parser.add_argument("--stream", required=True, help="stream name to backup")
    backup_parser.add_argument("--output", required=True, help="output directory")
    backup_parser.add_argument("--nats-url", help="nats server url")
    backup_parser.add_argument("--creds", help="creds file")
    backup_parser.add_argument("--context", help="nats context")
    backup_parser.add_argument("--nats-cli-path", help="path to nats CLI")

    restore_parser = subparsers.add_parser("restore", help="restore JetStream", parents=[common])
    restore_parser.add_argument("--input", required=True, help="input directory")
    restore_parser.add_argument("--confirm", action="store_true", help="confirm restore")
    restore_parser.add_argument("--nats-url", help="nats server url")
    restore_parser.add_argument("--creds", help="creds file")
    restore_parser.add_argument("--context", help="nats context")
    restore_parser.add_argument("--nats-cli-path", help="path to nats CLI")

    subparsers.add_parser("status", help="show status", parents=[common])
    doctor_parser = subparsers.add_parser("doctor", help="show diagnostics", parents=[common])
    doctor_parser.add_argument(
        "--controller",
        action="append",
        default=[],
        help="controller endpoint to check (e.g. http://127.0.0.1:8222)",
    )
    doctor_parser.add_argument(
        "--service-name",
        default=None,
        help="service name to check",
    )
    subparsers.add_parser("start", help="deprecated alias of up", parents=[common])

    return parser


def handle_with_binary(args: argparse.Namespace) -> int:
    try:
        config_path = Path(args.config) if args.config else default_config_path()
        if args.config and not config_path.exists():
            raise ConfigError("config file not found")
        config_result = load_config(config_path)
    except ConfigError as exc:
        print(f"{MSG_INVALID_CONFIG}: {exc}", file=sys.stderr)
        return 2

    try:
        resolved, attempts = resolve_binary_with_attempts(
            args.nats_server_path,
            config_result,
            os.environ,
        )
    except BinaryNotFoundError as exc:
        if args.command == "doctor":
            print("doctor: ng")
            print(f"binary: {MSG_NOT_FOUND}")
            print(f"config: {config_result.path} ({'exists' if config_result.exists else 'missing'})")
            print("resolution:")
            print_attempts(exc.attempts)
        else:
            print(MSG_NOT_FOUND, file=sys.stderr)
        return 2

    if args.command == "status":
        return handle_status(resolved, config_result)
    if args.command == "doctor":
        return handle_doctor(resolved, attempts, config_result, args)
    if args.command == "up":
        return handle_up(resolved, args)
    if args.command == "join":
        return handle_join(resolved, args)

    return 2


def handle_status(resolved, config_result) -> int:
    print("status: ok")
    print(f"nats-server: {resolved.path}")
    print(f"version: {resolved.version or 'unknown'}")
    print(f"source: {resolved.source}")
    print(f"config: {config_result.path} ({'exists' if config_result.exists else 'missing'})")
    return 0


def handle_doctor(resolved, attempts, config_result, args: argparse.Namespace) -> int:
    print("doctor: ok")
    print(f"nats-server: {resolved.path}")
    print(f"version: {resolved.version or 'unknown'}")
    print(f"source: {resolved.source}")
    print(f"config: {config_result.path} ({'exists' if config_result.exists else 'missing'})")
    print("priority:")
    print("- cli (--nats-server-path)")
    print("- config (--config or nats-config.json)")
    print("- env (NATS_SERVER_PATH, NATS_SERVER_BIN)")
    print("- nats-server-bin (extras)")
    print("- path (PATH)")
    print("resolution:")
    print_attempts(attempts)
    if args.controller:
        print("controller:")
        for endpoint in args.controller:
            ok = check_health(endpoint)
            state = "ok" if ok else "ng"
            print(f"- {endpoint}: {state}")
    pid_path = Path.cwd() / "nats-server.pid"
    pid_state = "exists" if pid_path.exists() else "missing"
    print(f"pid-file: {pid_path} ({pid_state})")
    try:
        nats_cli = resolve_nats_cli(None, os.environ)
        print(f"nats-cli: {nats_cli.path} ({nats_cli.source})")
    except NatsCliNotFoundError:
        print("nats-cli: not found")
    if args.service_name:
        if not is_windows():
            print(f"service: {args.service_name} ({MSG_SVC_UNSUPPORTED})")
        else:
            result = query_service(args.service_name)
            if result.returncode != 0:
                print(f"service: {args.service_name} (not found)")
            else:
                state = parse_service_state(result.stdout) or "unknown"
                print(f"service: {args.service_name} ({state})")
    return 0


def handle_controller(args: argparse.Namespace) -> int:
    if args.controller_command != "start":
        return not_implemented()

    sys_creds = Path(args.sys_creds)
    if not sys_creds.exists():
        print("controller error: sys.creds not found", file=sys.stderr)
        return 2

    state_dir = Path(args.state_dir) if args.state_dir else None
    config = ControllerConfig(
        listen=args.listen,
        nats_url=args.nats_url,
        sys_creds=sys_creds,
        state_dir=state_dir,
    )
    try:
        start_controller(config)
    except Exception as exc:
        print(f"controller error: {exc}", file=sys.stderr)
        return 2
    return 0


def handle_leave(args: argparse.Namespace) -> int:
    if not args.confirm:
        print(MSG_CONFIRM_REQUIRED, file=sys.stderr)
        return 2
    endpoints = list(args.controller or [])
    if not endpoints:
        print("controller endpoints are required", file=sys.stderr)
        return 2

    request_id = args.request_id or uuid.uuid4().hex
    server_name = args.server_name or socket.gethostname()
    payload = LeaveRequest(
        request_id=request_id,
        server_name=server_name,
        nats_url=args.nats_url,
    )

    try:
        response = call_leave(endpoints, payload)
    except ControllerUnavailableError:
        if args.stop_anyway:
            print("warning: controller unavailable (stop skipped in MVP)", file=sys.stderr)
            return 0
        print(MSG_CTRL_UNAVAILABLE, file=sys.stderr)
        return 2
    except ControllerRequestError as exc:
        print(f"{MSG_CTRL_INVALID}: {exc}", file=sys.stderr)
        return 2

    if response.result == "already_done":
        print("leave: already done")
    else:
        print("leave: ok")
    return handle_down(args)


def handle_down(args: argparse.Namespace) -> int:
    if not args.confirm:
        print(MSG_CONFIRM_REQUIRED, file=sys.stderr)
        return 2

    pid_path = Path.cwd() / "nats-server.pid"
    if not pid_path.exists():
        print("down: pid file not found (nats-server.pid)", file=sys.stderr)
        return 2

    try:
        pid_text = pid_path.read_text(encoding="utf-8").strip()
        pid = int(pid_text)
    except Exception:
        print("down: invalid pid file", file=sys.stderr)
        return 2

    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                check=False,
                capture_output=True,
                text=True,
            )
        else:
            os.kill(pid, 15)
    except Exception as exc:
        print(f"down: failed to stop pid {pid}: {exc}", file=sys.stderr)
        return 2

    print("down: ok")
    return 0


def _build_nats_cli_base(args: argparse.Namespace, cli_path: Path) -> list[str]:
    cmd = [str(cli_path)]
    if args.nats_url:
        cmd += ["--server", args.nats_url]
    if args.creds:
        cmd += ["--creds", args.creds]
    if args.context:
        cmd += ["--context", args.context]
    return cmd


def handle_backup(args: argparse.Namespace) -> int:
    try:
        nats_cli = resolve_nats_cli(args.nats_cli_path, os.environ)
    except NatsCliNotFoundError:
        print(MSG_BKP_NOT_FOUND, file=sys.stderr)
        return 2

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = _build_nats_cli_base(args, nats_cli.path)
    cmd += ["stream", "backup", args.stream, str(output_dir)]

    result = subprocess.run(cmd)
    return result.returncode


def handle_restore(args: argparse.Namespace) -> int:
    if not args.confirm:
        print(MSG_CONFIRM_REQUIRED, file=sys.stderr)
        return 2

    try:
        nats_cli = resolve_nats_cli(args.nats_cli_path, os.environ)
    except NatsCliNotFoundError:
        print(MSG_BKP_NOT_FOUND, file=sys.stderr)
        return 2

    input_dir = Path(args.input)
    if not input_dir.exists():
        print("restore: input directory not found", file=sys.stderr)
        return 2

    cmd = _build_nats_cli_base(args, nats_cli.path)
    cmd += ["stream", "restore", str(input_dir)]

    result = subprocess.run(cmd)
    return result.returncode


def handle_up(resolved, args: argparse.Namespace) -> int:
    if args.service:
        if not is_windows():
            print(MSG_SVC_UNSUPPORTED, file=sys.stderr)
            return 2
        result = start_service(args.service_name)
        if result.returncode != 0:
            if result.stdout:
                print(result.stdout.strip(), file=sys.stderr)
            if result.stderr:
                print(result.stderr.strip(), file=sys.stderr)
            return 2
        print("service: started")
        return 0

    nats_config, code = _resolve_bootstrap_config(args)
    if code != 0:
        return code

    extra_args = list(args.nats_args or [])
    if extra_args and extra_args[0] == "--":
        extra_args = extra_args[1:]

    return run_nats_server(resolved.path, nats_config, extra_args)


def handle_join(resolved, args: argparse.Namespace) -> int:
    return handle_up(resolved, args)


def _resolve_bootstrap_config(args: argparse.Namespace) -> tuple[str | None, int]:
    if not getattr(args, "cluster", None):
        return args.nats_config, 0

    if args.nats_config:
        print(MSG_BOOTSTRAP_CONFLICT, file=sys.stderr)
        return None, 2

    if args.command == "join" and not args.seed:
        print(MSG_BOOTSTRAP_SEED_REQUIRED, file=sys.stderr)
        return None, 2

    try:
        data_dir = resolve_data_dir(args.datafolder)
        generated = generate_bootstrap_config(
            args.cluster,
            data_dir,
            args.seed,
            client_port=args.client_port or DEFAULT_CLIENT_PORT,
            http_port=args.http_port or DEFAULT_HTTP_PORT,
            cluster_port=args.cluster_port or DEFAULT_CLUSTER_PORT,
            cluster_listen=args.listen,
        )
    except BootstrapConfigError as exc:
        msg = str(exc)
        if msg == "data folder is not a directory":
            msg = MSG_BOOTSTRAP_DATAFOLDER_INVALID
        elif msg == "cluster name is required":
            msg = MSG_BOOTSTRAP_CLUSTER_REQUIRED
        print(msg, file=sys.stderr)
        return None, 2

    return str(generated.path), 0


def run_nats_server(binary: Path, nats_config: str | None, extra_args: list[str]) -> int:
    cmd = [str(binary)]
    if nats_config:
        cmd += ["-c", nats_config]
    cmd += extra_args

    proc = subprocess.Popen(cmd)
    try:
        return proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        return 130


def print_attempts(attempts) -> None:
    for attempt in attempts:
        state = "ok" if attempt.ok else "ng"
        candidate = attempt.candidate or "-"
        reason = f" ({attempt.reason})" if attempt.reason else ""
        print(f"- {attempt.source}: {state} {candidate}{reason}")


def handle_service(args: argparse.Namespace) -> int:
    if not is_windows():
        print(MSG_SVC_UNSUPPORTED, file=sys.stderr)
        return 2

    if args.service_command == "install":
        try:
            config_path = Path(args.config) if args.config else default_config_path()
            if args.config and not config_path.exists():
                raise ConfigError("config file not found")
            config_result = load_config(config_path)
        except ConfigError as exc:
            print(f"{MSG_INVALID_CONFIG}: {exc}", file=sys.stderr)
            return 2

        try:
            resolved, _ = resolve_binary_with_attempts(
                args.nats_server_path,
                config_result,
                os.environ,
            )
        except BinaryNotFoundError:
            print(MSG_NOT_FOUND, file=sys.stderr)
            return 2

        if service_exists(args.service_name):
            print(MSG_SVC_EXISTS, file=sys.stderr)
            return 2

        bin_dir = Path(args.bin_dir) if args.bin_dir else None
        spec = ServiceInstallSpec(
            service_name=args.service_name,
            bin_dir=bin_dir,
            nats_config=args.nats_config,
        )
        result = install_service(spec, resolved.path)
        if result.returncode != 0:
            if result.stdout:
                print(result.stdout.strip(), file=sys.stderr)
            if result.stderr:
                print(result.stderr.strip(), file=sys.stderr)
            return 2

        if bin_dir is None:
            bin_path = build_service_binpath(resolved.path, args.nats_config)
            print(f"service installed (no copy): {bin_path}")
        else:
            target = (bin_dir / "nats-server.exe").resolve()
            print(f"service installed: {target}")
        return 0

    if args.service_command == "uninstall":
        if not service_exists(args.service_name):
            print(MSG_SVC_NOT_FOUND, file=sys.stderr)
            return 2
        result = uninstall_service(args.service_name)
        if result.returncode != 0:
            if result.stdout:
                print(result.stdout.strip(), file=sys.stderr)
            if result.stderr:
                print(result.stderr.strip(), file=sys.stderr)
            return 2
        print("service uninstalled")
        return 0

    return not_implemented()


def not_implemented() -> int:
    print(MSG_NOT_IMPLEMENTED, file=sys.stderr)
    return 2
