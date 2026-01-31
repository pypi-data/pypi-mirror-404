from __future__ import annotations

import logging
import re
from typing import Iterable

from logsentry_agent.config import PrivacyConfig

LOGGER = logging.getLogger(__name__)
REDACTED_VALUE = "[REDACTED]"
JWT_PATTERN = r"eyJ[a-zA-Z0-9_-]+\\.[a-zA-Z0-9_-]+\\.[a-zA-Z0-9_-]+"
API_KEY_PATTERN = r"(?i)(api[_-]?key|token)\\s*[:=]\\s*\\S+"


def compile_redact_patterns(patterns: Iterable[str]) -> list[re.Pattern]:
    compiled: list[re.Pattern] = []
    for pattern in patterns:
        try:
            compiled.append(re.compile(pattern))
        except re.error as exc:
            LOGGER.warning("Invalid redact pattern %s: %s", pattern, exc)
    return compiled


def redact_text(value: str, patterns: list[re.Pattern]) -> str:
    redacted = value
    for pattern in patterns:
        redacted = pattern.sub(REDACTED_VALUE, redacted)
    return redacted


def _redact_value(
    value: object,
    *,
    redact_keys: set[str],
    patterns: list[re.Pattern],
    allowlist: set[str],
    redacted_flag: list[bool],
) -> object:
    if isinstance(value, dict):
        sanitized: dict[str, object] = {}
        for key, val in value.items():
            if key.lower() in redact_keys and key.lower() not in allowlist:
                sanitized[key] = REDACTED_VALUE
                redacted_flag[0] = True
            else:
                sanitized[key] = _redact_value(
                    val,
                    redact_keys=redact_keys,
                    patterns=patterns,
                    allowlist=allowlist,
                    redacted_flag=redacted_flag,
                )
        return sanitized
    if isinstance(value, list):
        return [
            _redact_value(
                item,
                redact_keys=redact_keys,
                patterns=patterns,
                allowlist=allowlist,
                redacted_flag=redacted_flag,
            )
            for item in value
        ]
    if isinstance(value, str):
        redacted = redact_text(value, patterns)
        if redacted != value:
            redacted_flag[0] = True
        return redacted
    return value


def redact_event(
    event: dict,
    *,
    privacy: PrivacyConfig,
    allowlist: Iterable[str] | None = None,
    stats: dict[str, int] | None = None,
) -> dict:
    redact_keys = {key.lower() for key in privacy.field_redact_keys}
    combined_patterns = list(privacy.redact_patterns) + [JWT_PATTERN, API_KEY_PATTERN]
    patterns = compile_redact_patterns(combined_patterns)
    allowlist_set = {key.lower() for key in allowlist or []}
    redacted_flag = [False]
    sanitized = _redact_value(
        event,
        redact_keys=redact_keys,
        patterns=patterns,
        allowlist=allowlist_set,
        redacted_flag=redacted_flag,
    )
    if stats is not None and redacted_flag[0]:
        stats["redacted_count"] = stats.get("redacted_count", 0) + 1
    return sanitized
