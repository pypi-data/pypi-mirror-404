from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

COMMON_TIME_FORMATS: tuple[str, ...] = (
    "%d/%b/%Y:%H:%M:%S %z",  # Apache/Nginx
    "%Y-%m-%dT%H:%M:%S%z",  # ISO8601/RFC3339
    "%Y-%m-%d %H:%M:%S%z",
)

SYSLOG_TIME_FORMAT = "%b %d %H:%M:%S"
NOW_OVERRIDE: str | None = None


def _parse_with_formats(value: str, formats: Iterable[str]) -> datetime | None:
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def parse_timestamp(
    value: str | None,
    warnings: list[str] | None = None,
    *,
    now: datetime | None = None,
) -> str | None:
    if not value:
        if warnings is not None:
            warnings.append("missing timestamp")
        return None
    raw = value.strip()
    if not raw:
        if warnings is not None:
            warnings.append("empty timestamp")
        return None
    normalized = raw.replace("Z", "+00:00") if raw.endswith("Z") else raw
    parsed = None
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        parsed = _parse_with_formats(normalized, COMMON_TIME_FORMATS)
    if parsed is None:
        try:
            parsed = datetime.strptime(normalized, SYSLOG_TIME_FORMAT)
            now = now or datetime.now(timezone.utc)
            parsed = parsed.replace(year=now.year, tzinfo=timezone.utc)
        except ValueError:
            parsed = None
    if parsed is None:
        if warnings is not None:
            warnings.append(f"unparsed timestamp: {raw}")
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def now_utc_iso(now: datetime | None = None) -> str:
    if NOW_OVERRIDE is not None:
        return NOW_OVERRIDE
    current = now or datetime.now(timezone.utc)
    return current.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
