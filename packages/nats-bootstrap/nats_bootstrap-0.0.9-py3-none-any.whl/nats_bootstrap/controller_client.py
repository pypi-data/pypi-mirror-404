from __future__ import annotations

import json
from dataclasses import dataclass
from urllib import request
from urllib.error import URLError, HTTPError


@dataclass(frozen=True)
class LeaveRequest:
    request_id: str
    server_name: str
    nats_url: str | None = None


@dataclass(frozen=True)
class LeaveResponse:
    request_id: str
    result: str


class ControllerUnavailableError(RuntimeError):
    pass


class ControllerRequestError(RuntimeError):
    pass


def call_leave(endpoints: list[str], payload: LeaveRequest, timeout: float = 5.0) -> LeaveResponse:
    last_error: Exception | None = None
    for endpoint in endpoints:
        try:
            return _call_leave_single(endpoint, payload, timeout)
        except (ControllerUnavailableError, ControllerRequestError) as exc:
            last_error = exc
            continue
    raise ControllerUnavailableError("all controller endpoints failed") from last_error


def _call_leave_single(endpoint: str, payload: LeaveRequest, timeout: float) -> LeaveResponse:
    url = endpoint.rstrip("/") + "/v1/leave"
    body = json.dumps(
        {
            "request_id": payload.request_id,
            "server_name": payload.server_name,
            "nats_url": payload.nats_url,
        },
        ensure_ascii=True,
    ).encode("utf-8")
    req = request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except HTTPError as exc:
        raise ControllerRequestError(f"controller responded with {exc.code}") from exc
    except URLError as exc:
        raise ControllerUnavailableError("controller unreachable") from exc

    try:
        data = json.loads(raw)
    except Exception as exc:
        raise ControllerRequestError("invalid controller response") from exc

    if not isinstance(data, dict):
        raise ControllerRequestError("invalid controller response")

    request_id = data.get("request_id")
    result = data.get("result")
    if not isinstance(request_id, str) or not isinstance(result, str):
        raise ControllerRequestError("invalid controller response")
    return LeaveResponse(request_id=request_id, result=result)


def check_health(endpoint: str, timeout: float = 2.0) -> bool:
    url = endpoint.rstrip("/") + "/health"
    req = request.Request(url, method="GET")
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except Exception:
        return False
    try:
        data = json.loads(raw)
    except Exception:
        return False
    return isinstance(data, dict) and data.get("status") == "ok"
