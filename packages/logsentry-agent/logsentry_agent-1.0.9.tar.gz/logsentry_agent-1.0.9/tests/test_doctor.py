from argparse import Namespace
from hashlib import sha256
from pathlib import Path

from logsentry_agent.cli import cmd_doctor
from logsentry_agent.signer import sign_request


class FakeResponse:
    def __init__(self, status_code: int, headers: dict[str, str] | None = None):
        self.status_code = status_code
        self.headers: dict[str, str] = headers or {}


def _write_config(path: Path) -> None:
    path.write_text(
        """
agent_id: "agent"
shared_secret: "secret"
endpoint: "http://localhost:8002/v1/ingest"
""".strip(),
        encoding="utf-8",
    )


def test_doctor_uses_signed_head(monkeypatch, tmp_path: Path, capsys):
    config_path = tmp_path / "agent.yml"
    _write_config(config_path)

    fixed_time = 1_700_000_000
    fixed_nonce_bytes = b"\x01" * 12
    monkeypatch.setattr("logsentry_agent.cli.time.time", lambda: fixed_time)
    monkeypatch.setattr("logsentry_agent.cli.os.urandom", lambda n: fixed_nonce_bytes[:n])

    expected_timestamp = str(fixed_time)
    expected_nonce = f"{int.from_bytes(fixed_nonce_bytes, 'big'):024x}"
    expected_body_hash = sha256(b"").hexdigest()
    expected_signature = sign_request(
        "secret",
        "agent",
        expected_timestamp,
        expected_nonce,
        expected_body_hash,
    )

    def fake_head(endpoint, timeout, cert, verify, headers):  # noqa: ANN001
        assert endpoint == "http://localhost:8002/v1/ingest"
        assert timeout == 5
        assert cert is None
        assert verify is True
        assert headers["X-Agent-Id"] == "agent"
        assert headers["X-Agent-Timestamp"] == expected_timestamp
        assert headers["X-Agent-Nonce"] == expected_nonce
        assert headers["X-Agent-Content-SHA256"] == expected_body_hash
        assert headers["X-Agent-Signature"] == expected_signature
        return FakeResponse(405)

    monkeypatch.setattr("logsentry_agent.cli.requests.head", fake_head)

    rc = cmd_doctor(Namespace(config=config_path, command="doctor"))
    output = capsys.readouterr().out

    assert rc == 0
    assert "Endpoint reachable: 405" in output
    assert "rejected credentials" not in output.lower()


def test_doctor_counter_check_prints_resolved_agent(monkeypatch, tmp_path: Path, capsys):
    config_path = tmp_path / "agent.yml"
    _write_config(config_path)

    def fake_head(endpoint, timeout, cert, verify, headers):  # noqa: ANN001
        return FakeResponse(405, headers={"X-Resolved-Agent-Id": headers["X-Agent-Id"]})

    monkeypatch.setattr("logsentry_agent.cli.requests.head", fake_head)

    rc = cmd_doctor(Namespace(config=config_path, command="doctor", counter_check=True))
    output = capsys.readouterr().out

    assert rc == 0
    assert "Counter check — configured agent_id: agent" in output
    assert "Counter check — backend resolved agent_id: agent (match)" in output
