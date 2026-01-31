from pathlib import Path

from logsentry_agent.config import load_config


def test_shared_secret_file_used_when_secret_missing(tmp_path: Path):
    secret_path = tmp_path / "secret.txt"
    secret_path.write_text("file-secret\n", encoding="utf-8")

    config_path = tmp_path / "agent.yml"
    config_path.write_text(
        f"""
agent_id: "agent"
shared_secret: ""
shared_secret_file: "{secret_path}"
endpoint: "http://localhost:8002/v1/ingest"
""".strip(),
        encoding="utf-8",
    )

    config = load_config(config_path)
    assert config.shared_secret == "file-secret"
    assert config.shared_secret_file == secret_path


def test_shared_secret_takes_precedence(tmp_path: Path):
    secret_path = tmp_path / "secret.txt"
    secret_path.write_text("file-secret\n", encoding="utf-8")

    config_path = tmp_path / "agent.yml"
    config_path.write_text(
        f"""
agent_id: "agent"
shared_secret: "inline-secret"
shared_secret_file: "{secret_path}"
endpoint: "http://localhost:8002/v1/ingest"
""".strip(),
        encoding="utf-8",
    )

    config = load_config(config_path)
    assert config.shared_secret == "inline-secret"
