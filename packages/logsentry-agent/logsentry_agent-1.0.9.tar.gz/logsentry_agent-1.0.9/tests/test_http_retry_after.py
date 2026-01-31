from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

from logsentry_agent.config import SecurityConfig
from logsentry_agent.http import send_payload


class FakeResponse:
    def __init__(self, status_code: int, headers: dict | None = None):
        self.status_code = status_code
        self.headers = headers or {}


def test_retry_after_http_date(monkeypatch):
    retry_at = datetime.now(timezone.utc) + timedelta(seconds=5)
    header_value = format_datetime(retry_at)

    def fake_post(*args, **kwargs):  # noqa: ARG001
        return FakeResponse(429, {"Retry-After": header_value})

    monkeypatch.setattr("requests.post", fake_post)
    result = send_payload(
        endpoint="http://localhost:8002/v1/ingest",
        agent_id="agent",
        secret="secret",
        payload={"events": []},
        retry_max_seconds=10,
        security=SecurityConfig(require_tls=False),
    )
    assert result.status == "retry"
    assert result.retry_after_seconds is not None
    assert result.retry_after_seconds >= 0
