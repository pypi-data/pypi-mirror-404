import sys
from pathlib import Path

import pytest
from logsentry_agent import cli
from logsentry_agent.config import load_effective_config
from logsentry_agent.security import secret_fingerprint


def _write_config(path: Path, *, agent_id: str, secret: str, endpoint: str) -> None:
    path.write_text(
        f"""
agent_id: "{agent_id}"
shared_secret: "{secret}"
endpoint: "{endpoint}"
sources:
  - windows_eventlog
""".strip(),
        encoding="utf-8",
    )


def test_identity_output_is_sanitized(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys):
    config_path = tmp_path / "agent.yml"
    _write_config(
        config_path,
        agent_id="agent-123",
        secret="super-secret-value",
        endpoint="http://localhost:8002/v1/ingest",
    )

    monkeypatch.setattr(
        sys,
        "argv",
        ["logsentry-agent", "--config", str(config_path), "identity"],
    )

    with pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code == 0
    output = capsys.readouterr().out
    assert "super-secret-value" not in output
    assert f"Secret fingerprint: {secret_fingerprint('super-secret-value')}" in output


def test_provenance_env_over_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    config_path = tmp_path / "agent.yml"
    _write_config(
        config_path,
        agent_id="file-id",
        secret="file-secret",
        endpoint="http://localhost:8002/v1/ingest",
    )
    monkeypatch.setenv("LOGSENTRY_AGENT_ID", "env-id")

    effective = load_effective_config(config_path, allow_missing=True)

    assert effective.agent_id == "env-id"
    assert effective.provenance["agent_id"] == "env"


def test_run_print_identity_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys):
    config_path = tmp_path / "agent.yml"
    _write_config(
        config_path,
        agent_id="agent-456",
        secret="secret-value",
        endpoint="http://localhost:8002/v1/ingest",
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "logsentry-agent",
            "--config",
            str(config_path),
            "run",
            "--print-identity",
            "--once",
        ],
    )

    with pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code == 0
    output = capsys.readouterr().out
    assert "Config loaded from:" in output
    assert "Agent ID: agent-456" in output
