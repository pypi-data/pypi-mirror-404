from pathlib import Path

import pytest
from logsentry_agent.config import load_config


def test_env_expansion(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("LOGSENTRY_AGENT_SECRET", "env-secret")
    config_path = tmp_path / "agent.yml"
    config_path.write_text(
        """
agent_id: "agent"
shared_secret: "${LOGSENTRY_AGENT_SECRET}"
endpoint: "http://localhost:8002/v1/ingest"
""".strip(),
        encoding="utf-8",
    )

    config = load_config(config_path)
    assert config.shared_secret == "env-secret"


def test_env_expansion_default(tmp_path: Path):
    config_path = tmp_path / "agent.yml"
    config_path.write_text(
        """
agent_id: "agent"
shared_secret: "${MISSING_ENV:-fallback}"
endpoint: "http://localhost:8002/v1/ingest"
""".strip(),
        encoding="utf-8",
    )

    config = load_config(config_path)
    assert config.shared_secret == "fallback"


def test_env_expansion_missing_raises(tmp_path: Path):
    config_path = tmp_path / "agent.yml"
    config_path.write_text(
        """
agent_id: "agent"
shared_secret: "${MISSING_ENV}"
endpoint: "http://localhost:8002/v1/ingest"
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Missing environment variable"):
        load_config(config_path)


def test_env_expansion_placeholder_defaults_are_missing(tmp_path: Path):
    config_path = tmp_path / "agent.yml"
    config_path.write_text(
        """
agent_id: "${LOGSENTRY_AGENT_ID:-YOUR_AGENT_ID}"
shared_secret: "${LOGSENTRY_AGENT_SECRET:-YOUR_SHARED_SECRET}"
endpoint: "http://localhost:8002/v1/ingest"
""".strip(),
        encoding="utf-8",
    )

    config = load_config(config_path)
    assert not config.agent_id
    assert not config.shared_secret
