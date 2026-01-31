from __future__ import annotations

from logsentry_agent.normalize import apply_graceful_degradation
from logsentry_agent.utils.saferegex import compile_safe
from logsentry_agent.utils.timeparse import now_utc_iso, parse_timestamp

SYSLOG_PREFIX = compile_safe(
    r"^(?P<time>[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(?P<host>\S+)\s+sshd\[(?P<pid>\d+)\]:\s+(?P<msg>.+)$",
    prefix="sshd[",
)

FAILED_PASSWORD = compile_safe(
    r"Failed password for (invalid user )?(?P<user>\S+) from (?P<ip>\S+) port (?P<port>\d+) ssh2",
    prefix="Failed password",
)
FAILED_PUBLICKEY = compile_safe(
    r"Failed publickey for (invalid user )?(?P<user>\S+) from (?P<ip>\S+) port (?P<port>\d+) ssh2",
    prefix="Failed publickey",
)
ACCEPTED_PUBLICKEY = compile_safe(
    r"Accepted publickey for (?P<user>\S+) from (?P<ip>\S+) port (?P<port>\d+) ssh2",
    prefix="Accepted publickey",
)
ACCEPTED_PASSWORD = compile_safe(
    r"Accepted password for (?P<user>\S+) from (?P<ip>\S+) port (?P<port>\d+) ssh2",
    prefix="Accepted password",
)
CONNECTION_CLOSED = compile_safe(
    r"Connection closed by authenticating user (?P<user>\S+) (?P<ip>\S+) port (?P<port>\d+)",
    prefix="Connection closed",
)
CONNECTION_CLOSED_SIMPLE = compile_safe(
    r"Connection closed by (?P<ip>\S+) port (?P<port>\d+)",
    prefix="Connection closed",
)
INVALID_USER = compile_safe(
    r"Invalid user (?P<user>\S+) from (?P<ip>\S+) port (?P<port>\d+)",
    prefix="Invalid user",
)
RECEIVED_DISCONNECT = compile_safe(
    r"Received disconnect from (?P<ip>\S+) port (?P<port>\d+): (?P<reason>.+)",
    prefix="Received disconnect",
)
DISCONNECTED = compile_safe(
    r"Disconnected from (?P<ip>\S+) port (?P<port>\d+)",
    prefix="Disconnected",
)
PAM_FAILURE = compile_safe(
    r"pam_unix\(sshd:auth\): authentication failure;.*rhost=(?P<ip>\S+).*user=(?P<user>\S+)",
    prefix="pam_unix",
)
PAM_FAILURE_ALT = compile_safe(
    r"PAM: Authentication failure for (?P<user>\S+) from (?P<ip>\S+)",
    prefix="PAM:",
)


def parse_line(line: str) -> dict | None:
    line = line.strip()
    if not line:
        return None
    timestamp, message, pid, is_sshd = _extract_syslog(line)
    if not is_sshd and "sshd" not in line:
        return None
    warnings: list[str] = []
    if match := FAILED_PASSWORD.matches(message):
        return _build_auth_event(match, timestamp, pid, method="password", success=False)
    if match := FAILED_PUBLICKEY.matches(message):
        return _build_auth_event(match, timestamp, pid, method="publickey", success=False)
    if match := ACCEPTED_PUBLICKEY.matches(message):
        return _build_auth_event(match, timestamp, pid, method="publickey", success=True)
    if match := ACCEPTED_PASSWORD.matches(message):
        return _build_auth_event(match, timestamp, pid, method="password", success=True)
    if match := CONNECTION_CLOSED.matches(message):
        return _build_auth_event(
            match,
            timestamp,
            pid,
            method=None,
            success=False,
            action="auth.disconnect",
        )
    if match := CONNECTION_CLOSED_SIMPLE.matches(message):
        return _build_auth_event(
            match,
            timestamp,
            pid,
            method=None,
            success=False,
            action="auth.disconnect",
        )
    if match := INVALID_USER.matches(message):
        return _build_auth_event(
            match,
            timestamp,
            pid,
            method=None,
            success=False,
            action="auth.failure",
        )
    if match := RECEIVED_DISCONNECT.matches(message):
        return _build_auth_event(
            match,
            timestamp,
            pid,
            method=None,
            success=False,
            action="auth.disconnect",
        )
    if match := DISCONNECTED.matches(message):
        return _build_auth_event(
            match,
            timestamp,
            pid,
            method=None,
            success=False,
            action="auth.disconnect",
        )
    if match := PAM_FAILURE.matches(message):
        return _build_auth_event(
            match,
            timestamp,
            pid,
            method="pam",
            success=False,
            action="auth.failure",
        )
    if match := PAM_FAILURE_ALT.matches(message):
        return _build_auth_event(
            match,
            timestamp,
            pid,
            method="pam",
            success=False,
            action="auth.failure",
        )
    event = {
        "source": "ssh",
        "category": "auth",
        "action": "auth.unparsed",
        "severity": "low",
        "timestamp": timestamp or now_utc_iso(),
        "timestamp_quality": "source" if timestamp else "coerced",
        "parse": {
            "parser": "ssh_unparsed_v1",
            "confidence": 0.1,
            "warnings": warnings,
        },
    }
    return apply_graceful_degradation(event, raw_line=line)


def _extract_syslog(line: str) -> tuple[str | None, str, str | None, bool]:
    if match := SYSLOG_PREFIX.matches(line):
        timestamp = _parse_syslog_time(match.group("time"))
        return timestamp, match.group("msg"), match.group("pid"), True
    return None, line, None, False


def _parse_syslog_time(value: str) -> str | None:
    return parse_timestamp(value)


def _build_auth_event(
    match,
    timestamp: str | None,
    pid: str | None,
    *,
    method: str | None,
    success: bool,
    action: str | None = None,
) -> dict:
    data = match.groupdict()
    user = data.get("user")
    ip = data.get("ip")
    port = data.get("port")
    invalid_user = "invalid user" in match.group(0)
    action = action or ("auth.success" if success else "auth.failure")
    event = {
        "source": "ssh",
        "category": "auth",
        "action": action,
        "severity": "medium" if not success else "low",
        "timestamp": timestamp or now_utc_iso(),
        "timestamp_quality": "source" if timestamp else "coerced",
        "actor_ip": ip,
        "actor_user": user,
        "network": {"src_ip": ip, "src_port": int(port) if port else None, "protocol": "ssh"},
        "auth": {
            "method": method,
            "result": "success" if success else "failure",
            "is_invalid_user": invalid_user,
            "service": "sshd",
        },
        "process": {"pid": int(pid) if pid else None},
        "parse": {"parser": "ssh_auth_v1", "confidence": 0.9, "warnings": []},
    }
    return apply_graceful_degradation(event)
