from logsentry_agent.config import SecurityConfig
from logsentry_agent.http import send_payload


class FakeResponse:
    def __init__(self, status_code: int):
        self.status_code = status_code
        self.headers = {}


def test_tls_required_blocks_insecure_localhost_when_disallowed(monkeypatch):
    def fail_post(*args, **kwargs):  # noqa: ARG001
        raise AssertionError("request should not be attempted")

    monkeypatch.setattr("requests.post", fail_post)
    result = send_payload(
        endpoint="http://localhost:8002/v1/ingest",
        agent_id="agent",
        secret="secret",
        payload={"events": []},
        retry_max_seconds=10,
        security=SecurityConfig(require_tls=True, allow_insecure_localhost_http=False),
    )
    assert result.status == "fatal"


def test_tls_required_allows_localhost_when_enabled(monkeypatch):
    def fake_post(*args, **kwargs):  # noqa: ARG001
        return FakeResponse(200)

    monkeypatch.setattr("requests.post", fake_post)
    result = send_payload(
        endpoint="http://localhost:8002/v1/ingest",
        agent_id="agent",
        secret="secret",
        payload={"events": []},
        retry_max_seconds=10,
        security=SecurityConfig(require_tls=True, allow_insecure_localhost_http=True),
    )
    assert result.status == "ok"
