from logsentry_agent.config import SecurityConfig
from logsentry_agent.http import send_payload


class FakeResponse:
    def __init__(self, status_code: int, headers: dict | None = None):
        self.status_code = status_code
        self.headers = headers or {}


def test_retry_after_honored(monkeypatch):
    def fake_post(*args, **kwargs):  # noqa: ARG001
        return FakeResponse(429, {"Retry-After": "3"})

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
    assert result.retry_after_seconds == 3.0


def test_retry_after_missing_falls_back_to_backoff(monkeypatch):
    def fake_post(*args, **kwargs):  # noqa: ARG001
        return FakeResponse(429)

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
    assert result.retry_after_seconds is None


def test_auth_failure_is_fatal(monkeypatch):
    def fake_post(*args, **kwargs):  # noqa: ARG001
        return FakeResponse(401)

    monkeypatch.setattr("requests.post", fake_post)
    result = send_payload(
        endpoint="http://localhost:8002/v1/ingest",
        agent_id="agent",
        secret="secret",
        payload={"events": []},
        retry_max_seconds=10,
        security=SecurityConfig(require_tls=False),
    )
    assert result.status == "fatal"
    assert result.auth_failed is True


def test_server_error_is_retry(monkeypatch):
    def fake_post(*args, **kwargs):  # noqa: ARG001
        return FakeResponse(500)

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


def test_tls_required_rejects_insecure_endpoint():
    result = send_payload(
        endpoint="http://example.com/v1/ingest",
        agent_id="agent",
        secret="secret",
        payload={"events": []},
        retry_max_seconds=10,
        security=SecurityConfig(require_tls=True),
    )
    assert result.status == "fatal"
