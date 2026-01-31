from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.parse import urlsplit

from logsentry_agent.normalize import apply_graceful_degradation
from logsentry_agent.utils.saferegex import compile_safe
from logsentry_agent.utils.timeparse import now_utc_iso, parse_timestamp

COMBINED_RE = compile_safe(
    r"(?P<ip>[^\s]+) \S+ (?P<user>\S+) \[(?P<time>[^\]]+)\] "
    r'"(?P<method>\S+) (?P<path>\S+) [^"]+" '
    r"(?P<status>\d{3}) (?P<size>\d+|-) "
    r'"(?P<referrer>[^"]*)" "(?P<user_agent>[^"]*)"',
)
COMMON_RE = compile_safe(
    r"(?P<ip>[^\s]+) \S+ (?P<user>\S+) \[(?P<time>[^\]]+)\] "
    r'"(?P<method>\S+) (?P<path>\S+) [^"]+" '
    r"(?P<status>\d{3}) (?P<size>\d+|-)"
)

ERROR_RE = compile_safe(
    r"^\[(?P<time>[^\]]+)\] \[(?P<module>[^:]+):(?P<level>[^\]]+)\] "
    r"(?:\[pid (?P<pid>\d+)(?::tid \d+)?\] )?"
    r"(?:\[client (?P<client_ip>[^:\]]+)(?::(?P<client_port>\d+))?\] )?"
    r"(?P<message>.+)$",
    prefix="[",
)

SUSPICIOUS_TOKENS = ("../", "wp-admin", "phpmyadmin", "' or 1=1", "union select")


def parse_line(line: str) -> dict | None:
    line = line.strip()
    if not line:
        return None
    if line.startswith("{"):
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            return _unparsed_event(line, warnings=["invalid json"])
        return normalize_json(payload)
    match = ERROR_RE.matches(line)
    if match:
        return _build_error_event(match, line)
    match = COMBINED_RE.matches(line)
    parser = "apache_combined_v1"
    if not match:
        match = COMMON_RE.matches(line)
        parser = "apache_common_v1"
    if not match:
        return _unparsed_event(line, warnings=["unmatched line"])
    data = match.groupdict()
    warnings: list[str] = []
    timestamp = parse_timestamp(data.get("time"), warnings)
    path = data.get("path")
    http_path, http_query = _split_path(path)
    status = _safe_int(data.get("status"))
    size = _safe_int(data.get("size"))
    event = _build_http_event(
        parser=parser,
        confidence=0.92 if parser == "apache_combined_v1" else 0.90,
        warnings=warnings,
        timestamp=timestamp,
        actor_ip=data.get("ip"),
        actor_user=None if data.get("user") == "-" else data.get("user"),
        method=data.get("method"),
        path=http_path,
        query=http_query,
        status=status,
        size=size,
        referrer=data.get("referrer"),
        user_agent=data.get("user_agent"),
        vhost=None,
        latency_ms=None,
        raw_line=line,
    )
    return event


def normalize_json(payload: dict) -> dict:
    warnings: list[str] = []
    status = payload.get("status") or payload.get("status_code")
    timestamp = parse_timestamp(payload.get("time") or payload.get("timestamp"), warnings)
    request = payload.get("request")
    path = payload.get("request_uri") or payload.get("path")
    method = payload.get("request_method")
    if request and not path:
        parts = str(request).split()
        if len(parts) >= 2:
            method = method or parts[0]
            path = parts[1]
    http_path, http_query = _split_path(path)
    latency = _safe_float(payload.get("response_time") or payload.get("request_time"))
    size = _safe_int(payload.get("bytes_sent") or payload.get("body_bytes_sent"))
    vhost = payload.get("vhost") or payload.get("host")
    event = _build_http_event(
        parser="apache_json_v1",
        confidence=0.95,
        warnings=warnings,
        timestamp=timestamp,
        actor_ip=payload.get("remote_addr") or payload.get("client_ip"),
        actor_user=payload.get("remote_user"),
        method=method,
        path=http_path,
        query=http_query,
        status=_safe_int(status),
        size=size,
        referrer=payload.get("referrer"),
        user_agent=payload.get("user_agent"),
        vhost=vhost,
        latency_ms=latency,
        raw_line=None,
    )
    return event


def _unparsed_event(line: str, warnings: list[str]) -> dict:
    event = {
        "source": "apache",
        "category": "http",
        "action": "http.unparsed",
        "severity": "low",
        "timestamp": now_utc_iso(),
        "parse": {"parser": "apache_unparsed_v1", "confidence": 0.1, "warnings": warnings},
    }
    return apply_graceful_degradation(event, raw_line=line)


def _build_error_event(match, raw_line: str) -> dict:
    data = match.groupdict()
    timestamp = _parse_error_time(data.get("time"))
    message = data.get("message")
    severity = _severity_from_error(message)
    client_port = _safe_int(data.get("client_port"))
    event = {
        "source": "apache",
        "category": "http",
        "action": "http.error",
        "severity": severity,
        "timestamp": timestamp or now_utc_iso(),
        "timestamp_quality": "source" if timestamp else "coerced",
        "message": message,
        "network": {
            "src_ip": data.get("client_ip"),
            "src_port": client_port,
            "protocol": "http",
        },
        "process": {"pid": _safe_int(data.get("pid"))},
        "parse": {"parser": "apache_error_v1", "confidence": 0.9, "warnings": []},
    }
    return apply_graceful_degradation(event, raw_line=raw_line)


def _build_http_event(
    *,
    parser: str,
    confidence: float,
    warnings: list[str],
    timestamp: str | None,
    actor_ip: str | None,
    actor_user: str | None,
    method: str | None,
    path: str | None,
    query: str | None,
    status: int | None,
    size: int | None,
    referrer: str | None,
    user_agent: str | None,
    vhost: str | None,
    latency_ms: float | None,
    raw_line: str | None,
) -> dict:
    severity = _severity_from_status(status, path=path, query=query)
    event = {
        "source": "apache",
        "category": "http",
        "action": "http.request",
        "severity": severity,
        "timestamp": timestamp or now_utc_iso(),
        "timestamp_quality": "source" if timestamp else "coerced",
        "actor_ip": actor_ip,
        "actor_user": actor_user,
        "http": {
            "method": method,
            "path": path,
            "query": query,
            "status": status,
            "bytes": size,
            "referrer": referrer,
            "user_agent": user_agent,
            "vhost": vhost,
            "request_id": None,
            "latency_ms": latency_ms,
        },
        "network": {"src_ip": actor_ip, "protocol": "http"},
        "target": {"service": "apache", "resource": path},
        "parse": {"parser": parser, "confidence": confidence, "warnings": warnings},
    }
    return apply_graceful_degradation(event, raw_line=raw_line)


def _parse_error_time(value: str | None) -> str | None:
    if not value:
        return None
    try:
        parsed = datetime.strptime(value, "%a %b %d %H:%M:%S.%f %Y")
    except ValueError:
        return None
    parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _split_path(path: str | None) -> tuple[str | None, str | None]:
    if not path:
        return None, None
    parts = urlsplit(path)
    return parts.path or "/", parts.query or None


def _safe_int(value: str | int | None) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_float(value: str | float | None) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _severity_from_status(status: int | None, *, path: str | None, query: str | None) -> str:
    severity = "low"
    if status is None:
        severity = "low"
    elif status >= 500:
        severity = "high"
    elif status >= 400:
        severity = "medium"
    if path and any(token in path for token in SUSPICIOUS_TOKENS):
        severity = "high" if severity == "medium" else "medium"
    if query and any(token in query for token in SUSPICIOUS_TOKENS):
        severity = "high" if severity == "medium" else "medium"
    if status in (401, 403):
        severity = "medium"
    return severity


def _severity_from_error(message: str | None) -> str:
    if not message:
        return "low"
    lowered = message.lower()
    if "php fatal" in lowered:
        return "medium"
    if "ssl" in lowered or "tls" in lowered:
        return "medium"
    if "denied" in lowered or "access denied" in lowered:
        return "medium"
    return "low"
