from __future__ import annotations

from logsentry_agent.normalizers.windows_eventlog import normalize_event


def test_normalize_login_failed():
    record = {
        "event_id": 4625,
        "channel": "Security",
        "provider": "Microsoft-Windows-Security-Auditing",
        "timestamp": "2024-01-01T00:00:00+00:00",
        "event_data": {"TargetUserName": "bob", "IpAddress": "10.0.0.5", "LogonType": "3"},
        "computer": "WIN-01",
    }
    event = normalize_event(record)
    assert event["action"] == "auth.login_failed"
    assert event["category"] == "auth"
    assert event["actor_user"] == "bob"
    assert event["actor_ip"] == "10.0.0.5"
    assert event["auth"]["logon_type"] == "network"
    assert event["event_code"] == 4625
    assert event["event_id"]
    assert event["schema_version"] == "v1"


def test_normalize_service_install():
    record = {
        "event_id": 7045,
        "channel": "System",
        "provider": "Service Control Manager",
        "timestamp": "2024-01-01T00:00:00+00:00",
        "event_data": {"ServiceName": "ExampleSvc"},
        "computer": "WIN-01",
    }
    event = normalize_event(record)
    assert event["action"] == "system.service_installed"
    assert event["service"] == "ExampleSvc"
    assert event["event_code"] == 7045


def test_logon_type_mapping():
    record = {
        "event_id": 4624,
        "channel": "Security",
        "provider": "Microsoft-Windows-Security-Auditing",
        "timestamp": "2024-01-01T00:00:00+00:00",
        "event_data": {"TargetUserName": "alice", "IpAddress": "10.0.0.1", "LogonType": "10"},
        "computer": "WIN-01",
    }
    event = normalize_event(record)
    assert event["auth"]["logon_type"] == "remoteinteractive"
