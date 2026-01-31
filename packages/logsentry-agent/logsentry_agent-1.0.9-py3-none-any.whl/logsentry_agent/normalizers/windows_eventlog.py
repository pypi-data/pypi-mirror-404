from __future__ import annotations

import json
import xml.etree.ElementTree as ET

from logsentry_agent.config import PrivacyConfig
from logsentry_agent.normalize import apply_graceful_degradation
from logsentry_agent.redact import REDACTED_VALUE, redact_event
from logsentry_agent.utils.timeparse import parse_timestamp

_ACTION_MAP = {
    4624: ("auth.login_success", "auth", "low"),
    4625: ("auth.login_failed", "auth", "medium"),
    4634: ("auth.logout", "auth", "low"),
    4672: ("auth.privileged_logon", "auth", "high"),
    4688: ("process.started", "process", "medium"),
    7045: ("system.service_installed", "system", "medium"),
    4720: ("iam.account_created", "iam", "medium"),
    4722: ("iam.account_enabled", "iam", "medium"),
    4726: ("iam.account_deleted", "iam", "medium"),
    4732: ("iam.group_membership_added", "iam", "medium"),
    4104: ("script.powershell", "process", "medium"),
    1116: ("malware.detected", "security", "high"),
}

_CHANNEL_CATEGORY = {
    "security": "auth",
    "system": "system",
    "application": "application",
}

_LOGON_TYPE_MAP = {
    2: "interactive",
    3: "network",
    4: "batch",
    5: "service",
    7: "unlock",
    8: "networkcleartext",
    9: "newcredentials",
    10: "remoteinteractive",
    11: "cachedinteractive",
}


def _parse_event_xml(xml_data: str) -> dict[str, str]:
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError:
        return {}
    data = {}
    for elem in root.findall(".//EventData/Data"):
        name = elem.attrib.get("Name")
        if name:
            data[name] = elem.text or ""
    return data


def _extract_event_data(record: dict) -> dict[str, str]:
    if isinstance(record.get("event_data"), dict):
        return {str(k): str(v) for k, v in record["event_data"].items() if v is not None}
    if isinstance(record.get("event_xml"), str):
        return _parse_event_xml(record["event_xml"])
    return {}


def _map_logon_type(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return _LOGON_TYPE_MAP.get(int(value))
    except ValueError:
        return None


def _truncate_field(value: str, max_bytes: int) -> str:
    encoded = value.encode("utf-8")
    if len(encoded) <= max_bytes:
        return value
    return encoded[:max_bytes].decode("utf-8", errors="ignore")


def _ensure_max_bytes(event: dict, max_bytes: int) -> dict | None:
    payload_size = len(json.dumps(event, separators=(",", ":")).encode("utf-8"))
    if payload_size <= max_bytes:
        return event
    if isinstance(event.get("message"), str):
        event["message"] = _truncate_field(event["message"], max_bytes)
    if payload_size > max_bytes and isinstance(event.get("raw_event"), str):
        event["raw_event"] = _truncate_field(event["raw_event"], max_bytes)
    payload_size = len(json.dumps(event, separators=(",", ":")).encode("utf-8"))
    if payload_size <= max_bytes:
        return event
    if "raw_event" in event:
        event.pop("raw_event", None)
    payload_size = len(json.dumps(event, separators=(",", ":")).encode("utf-8"))
    if payload_size > max_bytes:
        return None
    return event


def normalize_event(
    record: dict,
    *,
    allow_raw: bool = False,
    redacted_fields: set[str] | None = None,
    event_max_bytes: int | None = None,
) -> dict | None:
    event_code = int(record.get("event_id", 0))
    action, category, severity = _ACTION_MAP.get(
        event_code,
        (
            "event.generic",
            _CHANNEL_CATEGORY.get(str(record.get("channel", "")).lower(), "system"),
            "low",
        ),
    )
    event_data = _extract_event_data(record)
    logon_type = _map_logon_type(event_data.get("LogonType"))
    actor_user = event_data.get("SubjectUserName") or record.get("user")
    target_user = event_data.get("TargetUserName")
    if event_code in {4624, 4625, 4634} and target_user:
        actor_user = target_user
    actor_ip = event_data.get("IpAddress") or record.get("ip")
    auth_method = event_data.get("AuthenticationPackageName")
    confidence = 0.1
    parser = "windows_eventlog_unparsed_v1"
    if event_code in _ACTION_MAP and event_data:
        confidence = 0.95
        parser = "windows_eventlog_structured_v1"
    elif event_code in _ACTION_MAP:
        confidence = 0.60
        parser = "windows_eventlog_fallback_v1"
    severity_override = severity
    if event_code == 4625 and actor_ip:
        severity_override = "medium"
    if event_code == 4672:
        severity_override = "high"
    if event_code == 1116:
        severity_override = "high"
    process_name = event_data.get("NewProcessName") or event_data.get("ProcessName")
    command_line = event_data.get("CommandLine") or event_data.get("ScriptBlockText")
    if redacted_fields and "command_line" in {field.lower() for field in redacted_fields}:
        if command_line:
            command_line = REDACTED_VALUE
    timestamp = parse_timestamp(record.get("timestamp")) or record.get("timestamp")
    event = {
        "source": "windows_eventlog",
        "category": category,
        "action": action,
        "severity": severity_override,
        "timestamp": timestamp,
        "actor_user": actor_user,
        "actor_ip": actor_ip,
        "target_user": target_user,
        "host": {"hostname": record.get("computer"), "fingerprint": None},
        "event_code": event_code,
        "channel": record.get("channel"),
        "provider": record.get("provider"),
        "auth": {
            "logon_type": logon_type,
            "method": auth_method,
            "result": (
                "failure" if event_code == 4625 else "success" if event_code == 4624 else None
            ),
        },
        "process": {
            "name": process_name,
            "command_line": command_line,
            "parent": event_data.get("ParentProcessName"),
        },
        "service": event_data.get("ServiceName"),
        "malware": {
            "name": event_data.get("ThreatName"),
            "severity": event_data.get("Severity"),
        }
        if event_code == 1116
        else None,
        "iam": {
            "group": event_data.get("GroupName"),
            "subject_user": event_data.get("SubjectUserName"),
        }
        if event_code in {4720, 4722, 4726, 4732}
        else None,
        "parse": {
            "parser": parser,
            "confidence": confidence,
            "warnings": [],
        },
    }
    if allow_raw:
        redacted_fields = redacted_fields or set()
        raw_event = {
            key: value for key, value in record.items() if key.lower() not in redacted_fields
        }
        event["raw_event"] = json.dumps(raw_event, separators=(",", ":"))
        event["message"] = record.get("message")
    normalized = apply_graceful_degradation(event)
    if allow_raw:
        normalized = redact_event(normalized, privacy=PrivacyConfig(allow_raw=True))
    if event_max_bytes is not None:
        return _ensure_max_bytes(normalized, event_max_bytes)
    return normalized
