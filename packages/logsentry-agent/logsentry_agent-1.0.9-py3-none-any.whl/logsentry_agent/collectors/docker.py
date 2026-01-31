from __future__ import annotations

import json

from logsentry_agent.normalize import apply_graceful_degradation
from logsentry_agent.utils.multiline import MultilineBuffer
from logsentry_agent.utils.timeparse import now_utc_iso, parse_timestamp

_MULTILINE_BUFFERS: dict[str, MultilineBuffer] = {}


def parse_line(
    line: str,
    *,
    container: str,
    image: str | None = None,
    enable_multiline: bool = False,
    flush: bool = False,
) -> dict | list[dict] | None:
    if enable_multiline and flush:
        buffer = _MULTILINE_BUFFERS.setdefault(container, MultilineBuffer())
        flushed = buffer.flush()
        if flushed is None:
            return None
        return _build_event(
            flushed,
            None,
            container=container,
            image=image,
            stream=None,
            raw_line=line,
        )
    line = line.strip()
    if not line:
        return None
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        return _build_unparsed_event(
            line,
            container=container,
            image=image,
            warnings=["invalid json"],
        )
    if not isinstance(payload, dict):
        return _build_unparsed_event(
            line,
            container=container,
            image=image,
            warnings=["invalid payload"],
        )
    message = (payload.get("log") or payload.get("message") or "").rstrip("\n")
    timestamp = parse_timestamp(payload.get("time") or payload.get("timestamp"))
    stream = payload.get("stream")
    if not message:
        return _build_unparsed_event(
            line,
            container=container,
            image=image,
            warnings=["missing message"],
        )
    if enable_multiline:
        buffer = _MULTILINE_BUFFERS.setdefault(container, MultilineBuffer())
        completed = buffer.feed(message)
        events: list[dict] = []
        for entry in completed:
            events.append(
                _build_event(
                    entry,
                    timestamp,
                    container=container,
                    image=image,
                    stream=stream,
                    raw_line=line,
                )
            )
        return events or None
    return _build_event(
        message,
        timestamp,
        container=container,
        image=image,
        stream=stream,
        raw_line=line,
    )


def _build_event(
    message: str,
    timestamp: str | None,
    *,
    container: str,
    image: str | None,
    stream: str | None,
    raw_line: str | None,
) -> dict:
    container_meta = _container_metadata(container)
    severity = _severity_from_message(message)
    event = {
        "source": f"docker:{container}",
        "category": "process",
        "action": "container.log",
        "severity": severity,
        "timestamp": timestamp or now_utc_iso(),
        "timestamp_quality": "source" if timestamp else "coerced",
        "message": message,
        "container": {
            **container_meta,
            "image": image,
            "stream": stream,
        },
        "parse": {"parser": "docker_json_v1", "confidence": 0.9, "warnings": []},
    }
    return apply_graceful_degradation(event, raw_line=raw_line)


def _build_unparsed_event(
    line: str,
    *,
    container: str,
    image: str | None,
    warnings: list[str],
) -> dict:
    container_meta = _container_metadata(container)
    event = {
        "source": f"docker:{container}",
        "category": "process",
        "action": "container.unparsed",
        "severity": "low",
        "timestamp": now_utc_iso(),
        "timestamp_quality": "coerced",
        "message": line,
        "container": {
            **container_meta,
            "image": image,
            "stream": None,
        },
        "parse": {"parser": "docker_unparsed_v1", "confidence": 0.1, "warnings": warnings},
    }
    return apply_graceful_degradation(event, raw_line=line)


def _container_metadata(container: str) -> dict:
    container_id = container if _is_container_id(container) else None
    return {
        "id": container_id,
        "name": container,
        "labels": None,
        "service": None,
    }


def _is_container_id(value: str) -> bool:
    return len(value) in {12, 64} and all(ch in "0123456789abcdef" for ch in value.lower())


def _severity_from_message(message: str) -> str:
    trimmed = message.lstrip()
    upper = trimmed.upper()
    if upper.startswith("ERROR"):
        return "high"
    if upper.startswith("WARN"):
        return "medium"
    if upper.startswith("INFO"):
        return "low"
    return "low"
