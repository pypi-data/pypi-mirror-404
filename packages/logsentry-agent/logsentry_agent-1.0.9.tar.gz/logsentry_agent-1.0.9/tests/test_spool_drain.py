from pathlib import Path

import requests
from logsentry_agent.config import (
    AgentConfig,
    ApacheConfig,
    DockerConfig,
    NginxConfig,
    PrivacyConfig,
    ReliabilityConfig,
    SecurityConfig,
    SshConfig,
    WindowsEventLogConfig,
)
from logsentry_agent.http import SendResult
from logsentry_agent.run import _drain_spool_batch
from logsentry_agent.spool import SpoolQueue


def _build_config(tmp_path: Path) -> AgentConfig:
    return AgentConfig(
        agent_id="agent",
        shared_secret="secret",
        shared_secret_file=None,
        endpoint="http://localhost:8002/v1/ingest",
        log_dir=None,
        spool_path=tmp_path / "spool.db",
        spool_max_mb=1,
        retry_max_seconds=10,
        max_in_flight=10,
        batch_size=10,
        flush_interval_ms=1000,
        queue_max_size=100,
        spool_drop_policy="drop_oldest",
        state_path=tmp_path / "state.json",
        sources=[],
        allow_raw=False,
        privacy=PrivacyConfig(),
        security=SecurityConfig(require_tls=False),
        reliability=ReliabilityConfig(spool_drain_batch_size=10, spool_drain_interval_ms=500),
        health_interval_seconds=60,
        windows_eventlog=WindowsEventLogConfig(),
        nginx=NginxConfig(),
        apache=ApacheConfig(),
        ssh=SshConfig(),
        docker=DockerConfig(),
    )


def test_spool_drain_recovers_after_failure(tmp_path: Path):
    config = _build_config(tmp_path)
    spool = SpoolQueue(config.spool_path, max_mb=1)
    spool.enqueue({"events": [{"event_id": "1"}]})
    spool.enqueue({"events": [{"event_id": "2"}]})

    calls = {"count": 0}

    def fake_send(*args, **kwargs):  # noqa: ARG001
        calls["count"] += 1
        if calls["count"] == 1:
            return SendResult(status="retry")
        return SendResult(status="ok")

    ids, result, sent = _drain_spool_batch(spool=spool, config=config, send_fn=fake_send)
    assert ids == []
    assert result is not None
    assert result.status == "retry"
    assert sent == 0
    assert spool.pending_count() == 2

    ids, result, sent = _drain_spool_batch(spool=spool, config=config, send_fn=fake_send)
    assert result is not None
    assert result.status == "ok"
    assert sent == 2
    assert spool.pending_count() == 0


def test_spool_drain_respects_percent_limit(tmp_path: Path):
    config = _build_config(tmp_path)
    config.reliability = ReliabilityConfig(
        spool_drain_batch_size=10,
        spool_drain_interval_ms=500,
        spool_drain_percent=40,
    )
    spool = SpoolQueue(config.spool_path, max_mb=1)
    for index in range(10):
        spool.enqueue({"events": [{"event_id": str(index)}]})

    def fake_send(*args, **kwargs):  # noqa: ARG001
        return SendResult(status="ok")

    ids, result, sent = _drain_spool_batch(spool=spool, config=config, send_fn=fake_send)
    assert result is not None
    assert result.status == "ok"
    assert sent == 4
    assert len(ids) == 4
    assert spool.pending_count() == 6


def test_spool_drain_splits_invalid_batch(tmp_path: Path):
    config = _build_config(tmp_path)
    spool = SpoolQueue(config.spool_path, max_mb=1)
    spool.enqueue({"events": [{"event_id": "1"}, {"event_id": "2"}]})

    response = requests.Response()
    response.status_code = 400

    def fake_send(*args, **kwargs):  # noqa: ARG001
        payload = kwargs.get("payload", {})
        events = payload.get("events", [])
        if len(events) > 1:
            return SendResult(status="retry", response=response)
        if events and events[0].get("event_id") == "1":
            return SendResult(status="ok")
        return SendResult(status="retry", response=response)

    ids, result, sent = _drain_spool_batch(spool=spool, config=config, send_fn=fake_send)
    assert ids == [1]
    assert result is not None
    assert result.status == "ok"
    assert sent == 1
    assert spool.pending_count() == 0
