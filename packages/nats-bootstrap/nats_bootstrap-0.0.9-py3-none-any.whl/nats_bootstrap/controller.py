from __future__ import annotations

from dataclasses import dataclass
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import time


DEFAULT_LISTEN = "127.0.0.1:8222"


@dataclass(frozen=True)
class ControllerConfig:
    listen: str
    nats_url: str
    sys_creds: Path
    state_dir: Path | None = None


class ControllerState:
    def __init__(self, state_dir: Path) -> None:
        self._state_dir = state_dir
        self._state_file = state_dir / "controller_state.json"
        self._lock = threading.Lock()
        self._data = {"requests": {}}
        self._load()

    def _load(self) -> None:
        if not self._state_file.exists():
            return
        try:
            raw = json.loads(self._state_file.read_text(encoding="utf-8"))
        except Exception:
            return
        if isinstance(raw, dict) and isinstance(raw.get("requests"), dict):
            self._data = raw

    def _save(self) -> None:
        self._state_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = self._state_file.with_suffix(".tmp")
        tmp_path.write_text(
            json.dumps(self._data, ensure_ascii=True, separators=(",", ":")),
            encoding="utf-8",
        )
        tmp_path.replace(self._state_file)

    def get(self, request_id: str) -> dict | None:
        with self._lock:
            return self._data.get("requests", {}).get(request_id)

    def record(self, request_id: str, payload: dict) -> None:
        with self._lock:
            self._data.setdefault("requests", {})[request_id] = payload
            self._save()


def default_state_dir() -> Path:
    return Path.home() / ".nats-bootstrap" / "controller"


def parse_listen(listen: str) -> tuple[str, int]:
    if ":" not in listen:
        raise ValueError("listen must be <host:port>")
    host, port_text = listen.rsplit(":", 1)
    if not host:
        host = "127.0.0.1"
    port = int(port_text)
    return host, port


def start_controller(config: ControllerConfig) -> None:
    state_dir = config.state_dir or default_state_dir()
    state = ControllerState(state_dir)
    host, port = parse_listen(config.listen)
    handler = _make_handler(state)
    server = ThreadingHTTPServer((host, port), handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def _make_handler(state: ControllerState):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

        def _send_json(self, status: int, payload: dict) -> None:
            body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            if self.path != "/health":
                self.send_error(404)
                return
            self._send_json(200, {"status": "ok"})

        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/v1/leave":
                self.send_error(404)
                return

            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length > 0 else b""
            try:
                data = json.loads(raw.decode("utf-8"))
            except Exception:
                self._send_json(400, {"error": "invalid_request"})
                return

            if not isinstance(data, dict):
                self._send_json(400, {"error": "invalid_request"})
                return

            request_id = data.get("request_id")
            server_name = data.get("server_name")
            nats_url = data.get("nats_url")

            if not isinstance(request_id, str) or not request_id:
                self._send_json(400, {"error": "invalid_request"})
                return
            if not isinstance(server_name, str) or not server_name:
                self._send_json(400, {"error": "invalid_request"})
                return
            if nats_url is not None and not isinstance(nats_url, str):
                self._send_json(400, {"error": "invalid_request"})
                return

            existing = state.get(request_id)
            if existing:
                self._send_json(200, {"request_id": request_id, "result": "already_done"})
                return

            payload = {
                "request_id": request_id,
                "server_name": server_name,
                "nats_url": nats_url,
                "timestamp": int(time.time()),
            }
            state.record(request_id, payload)
            self._send_json(200, {"request_id": request_id, "result": "ok"})

    return Handler
