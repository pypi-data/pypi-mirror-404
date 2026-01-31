from __future__ import annotations

import socket
from uuid import uuid4

from logsentry_agent.utils.timeparse import now_utc_iso


def apply_graceful_degradation(
    event: dict,
    *,
    raw_line: str | None = None,
    parser: str = "unknown",
    confidence: float = 1.0,
    schema_version: str = "v1",
) -> dict:
    normalized = event.copy()
    if not normalized.get("event_id"):
        normalized["event_id"] = str(uuid4())
    if not normalized.get("schema_version"):
        normalized["schema_version"] = schema_version
    if "parse" not in normalized:
        normalized["parse"] = {"parser": parser, "confidence": confidence, "warnings": []}
    else:
        normalized["parse"].setdefault("parser", parser)
        normalized["parse"].setdefault("confidence", confidence)
        normalized["parse"].setdefault("warnings", [])
    if not normalized.get("timestamp"):
        normalized["timestamp"] = now_utc_iso()
        normalized["timestamp_quality"] = "derived"
        if "parse" in normalized:
            normalized["parse"]["confidence"] = min(
                float(normalized["parse"].get("confidence", confidence)),
                0.3,
            )
    else:
        normalized.setdefault("timestamp_quality", "source")
    normalized.setdefault("source", None)
    normalized.setdefault("category", None)
    normalized.setdefault("action", None)
    normalized.setdefault("severity", None)
    hostname = None
    if isinstance(normalized.get("host"), dict):
        hostname = normalized["host"].get("hostname")
    if not hostname:
        hostname = normalized.get("hostname") or socket.gethostname()
    if "host" not in normalized or not isinstance(normalized.get("host"), dict):
        normalized["host"] = {"hostname": hostname, "fingerprint": None}
    else:
        normalized["host"].setdefault("hostname", hostname)
        normalized["host"].setdefault("fingerprint", None)
    normalized.setdefault(
        "actor",
        {
            "ip": normalized.get("actor_ip"),
            "user": normalized.get("actor_user"),
        },
    )
    normalized.setdefault(
        "target",
        {
            "user": normalized.get("target_user"),
            "service": normalized.get("target_service"),
            "resource": normalized.get("target_path"),
        },
    )
    normalized.setdefault(
        "network",
        {
            "src_ip": normalized.get("actor_ip"),
            "src_port": normalized.get("src_port"),
            "dst_ip": normalized.get("dst_ip"),
            "dst_port": normalized.get("dst_port"),
            "protocol": normalized.get("protocol"),
        },
    )
    normalized.setdefault(
        "http",
        {
            "method": normalized.get("method"),
            "path": normalized.get("path") or normalized.get("target_path"),
            "query": normalized.get("query"),
            "status": normalized.get("status"),
            "bytes": normalized.get("bytes"),
            "referrer": normalized.get("referrer"),
            "user_agent": normalized.get("user_agent"),
            "vhost": normalized.get("vhost"),
            "request_id": normalized.get("request_id"),
            "latency_ms": normalized.get("latency_ms"),
        },
    )
    if "actor_user" not in normalized:
        normalized["actor_user"] = None
    if "actor_ip" not in normalized:
        normalized["actor_ip"] = None
    if raw_line and "raw_line" not in normalized:
        normalized["raw_line"] = raw_line
    return normalized
