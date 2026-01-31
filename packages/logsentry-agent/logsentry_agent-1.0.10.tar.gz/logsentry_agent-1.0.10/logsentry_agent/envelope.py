from __future__ import annotations

import socket
import sys
from datetime import datetime, timezone
from uuid import uuid4

from logsentry_agent.fingerprint import compute_fingerprint

_PRIORITY_ORDER = ["raw", "info", "low", "medium", "high", "critical"]


def build_envelope(
    *, version: str, events: list[dict], seq: int, schema_version: str = "v1"
) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "schema_version": schema_version,
        "agent": {
            "version": version,
            "platform": sys.platform,
            "hostname": socket.gethostname(),
        },
        "envelope": {
            "id": str(uuid4()),
            "seq": seq,
            "created_at": now.isoformat(),
        },
        "agent_time_utc": now.isoformat(),
        "agent_time_unix": int(now.timestamp()),
        "host": {
            "fingerprint": compute_fingerprint(),
        },
        "events": events,
    }


def compute_priority(events: list[dict]) -> str:
    best_index = 0
    for event in events:
        severity = str(event.get("severity", "low")).lower()
        if severity not in _PRIORITY_ORDER:
            continue
        best_index = max(best_index, _PRIORITY_ORDER.index(severity))
    return _PRIORITY_ORDER[best_index]
