from __future__ import annotations

import importlib.util
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Iterable

from logsentry_agent.config import WindowsEventLogConfig
from logsentry_agent.normalizers import windows_eventlog as windows_eventlog_normalizer
from logsentry_agent.state import AgentState

if importlib.util.find_spec("win32evtlog") is not None:  # pragma: no cover - optional dependency
    import pywintypes
    import win32evtlog
    import win32security
else:  # pragma: no cover - optional dependency
    win32evtlog = None
    win32security = None
    pywintypes = None


LEVEL_ORDER = {
    "Critical": 4,
    "Error": 3,
    "Warning": 2,
    "Information": 1,
}

normalize_event = windows_eventlog_normalizer.normalize_event


@dataclass
class WindowsCollectorStats:
    events_collected: int = 0
    access_denied: int = 0
    dropped_too_large: int = 0
    last_bookmarks: dict[str, int] = field(default_factory=dict)


class WindowsEventLogReader:
    def __init__(self, config: WindowsEventLogConfig, state: AgentState) -> None:
        self.config = config
        self.state = state
        self._handles: dict[str, object] = {}
        self._start_records: dict[str, int] = {}

    def poll(self) -> tuple[list[dict], WindowsCollectorStats]:
        if win32evtlog is None:
            raise RuntimeError(
                "pywin32 is required for Windows Event Log collection. "
                "Install with `pip install logsentry-agent[windows]`."
            )
        stats = WindowsCollectorStats()
        events: list[dict] = []
        for channel in self.config.channels:
            try:
                handle = self._get_handle(channel)
            except PermissionError:
                stats.access_denied += 1
                continue
            start_record = self._determine_start_record(channel, handle)
            last_timestamp = None
            for record in self._read_records(handle, start_record, channel):
                if not self._passes_filters(record):
                    continue
                events.append(record)
                stats.events_collected += 1
                stats.last_bookmarks[channel] = record["record_number"]
                last_timestamp = record["timestamp"]
                if len(events) >= self.config.max_events_per_poll:
                    break
            if channel in stats.last_bookmarks:
                self.state.update_checkpoint(
                    channel,
                    stats.last_bookmarks[channel],
                    last_timestamp or datetime.now(timezone.utc).isoformat(),
                )
                self._start_records[channel] = stats.last_bookmarks[channel] + 1
        return events, stats

    def _get_handle(self, channel: str):
        if channel in self._handles:
            return self._handles[channel]
        try:
            handle = win32evtlog.OpenEventLog(None, channel)
        except pywintypes.error as exc:
            if exc.winerror == 5:
                raise PermissionError(channel) from exc
            raise
        self._handles[channel] = handle
        return handle

    def _determine_start_record(self, channel: str, handle) -> int:
        if channel in self._start_records:
            return self._start_records[channel]
        total = win32evtlog.GetNumberOfEventLogRecords(handle)
        oldest = win32evtlog.GetOldestEventLogRecord(handle)
        checkpoint = self.state.get_checkpoint(channel)
        if checkpoint:
            record = int(checkpoint.get("record_number", oldest))
            if record < oldest or record > oldest + total:
                record = oldest + max(total - 1, 0)
            start_record = record + 1
        else:
            if self.config.start_mode == "from_record" and self.config.from_record:
                start_record = max(int(self.config.from_record), oldest)
            elif self.config.start_mode == "since_minutes":
                start_record = oldest
            else:
                start_record = oldest + max(total - 1, 0)
        self._start_records[channel] = start_record
        return start_record

    def _read_records(self, handle, start_record: int, channel: str) -> Iterable[dict]:
        flags = win32evtlog.EVENTLOG_FORWARDS_READ | win32evtlog.EVENTLOG_SEEK_READ
        record_number = start_record
        read_events = 0
        while read_events < self.config.max_events_per_poll:
            try:
                records = win32evtlog.ReadEventLog(handle, flags, record_number)
            except pywintypes.error:
                break
            if not records:
                break
            for event in records:
                record_number = event.RecordNumber + 1
                read_events += 1
                yield self._convert_event(event, record_number - 1, channel)
                if read_events >= self.config.max_events_per_poll:
                    break

    def _convert_event(self, event, record_number: int, channel: str) -> dict:
        timestamp = self._format_timestamp(event.TimeGenerated)
        user = None
        if event.Sid and win32security is not None:
            try:
                name, domain, _ = win32security.LookupAccountSid(None, event.Sid)
                user = f"{domain}\\{name}" if domain else name
            except pywintypes.error:
                user = None
        message = ""
        if getattr(event, "StringInserts", None):
            message = " ".join(str(item) for item in event.StringInserts if item)
        return {
            "event_id": int(event.EventID & 0xFFFF),
            "channel": channel,
            "provider": event.SourceName,
            "timestamp": timestamp,
            "record_number": record_number,
            "computer": event.ComputerName,
            "level": self._event_type_to_level(event.EventType),
            "message": message,
            "strings": list(event.StringInserts or []),
            "user": user,
        }

    def _format_timestamp(self, value) -> str:
        if hasattr(value, "isoformat"):
            dt = value
            if getattr(dt, "tzinfo", None) is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        return datetime.now(timezone.utc).isoformat()

    def _event_type_to_level(self, event_type: int) -> str:
        if event_type == win32evtlog.EVENTLOG_ERROR_TYPE:
            return "Error"
        if event_type == win32evtlog.EVENTLOG_WARNING_TYPE:
            return "Warning"
        if event_type == win32evtlog.EVENTLOG_AUDIT_FAILURE:
            return "Error"
        return "Information"

    def _passes_filters(self, record: dict) -> bool:
        if self.config.event_id_allow and record["event_id"] not in self.config.event_id_allow:
            return False
        if record["event_id"] in self.config.event_id_deny:
            return False
        if self.config.provider_allow and record["provider"] not in self.config.provider_allow:
            return False
        if record["provider"] in self.config.provider_deny:
            return False
        min_level = LEVEL_ORDER.get(self.config.level_min, 1)
        record_level = LEVEL_ORDER.get(record.get("level", "Information"), 1)
        return record_level >= min_level


def should_filter_since(record: dict, since_minutes: int) -> bool:
    try:
        timestamp = datetime.fromisoformat(record["timestamp"])
    except ValueError:
        return False
    return timestamp < datetime.now(timezone.utc) - timedelta(minutes=since_minutes)
