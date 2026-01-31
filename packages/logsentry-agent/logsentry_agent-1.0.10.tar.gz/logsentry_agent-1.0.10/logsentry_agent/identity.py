from __future__ import annotations

import getpass
import os

from logsentry_agent.config import EffectiveConfig
from logsentry_agent.security import secret_fingerprint


def _format_user() -> str:
    user = getpass.getuser()
    if os.name == "nt":
        username = os.environ.get("USERNAME")
        domain = os.environ.get("USERDOMAIN")
        if domain and username:
            return f"{domain}\\{username}"
        if username:
            return username
    return user


def required_fields_missing(config: EffectiveConfig) -> list[str]:
    missing = []
    if not config.agent_id:
        missing.append("agent_id")
    if not config.shared_secret:
        missing.append("shared_secret")
    if not config.endpoint:
        missing.append("endpoint")
    return missing


def identity_exit_code(config: EffectiveConfig) -> int:
    return 0 if not required_fields_missing(config) else 2


def identity_summary(config: EffectiveConfig) -> dict[str, str]:
    return {
        "agent_id": config.agent_id or "missing",
        "endpoint": config.endpoint or "missing",
        "secret_fp": secret_fingerprint(config.shared_secret or ""),
        "secret_src": config.provenance.get("shared_secret", "missing"),
        "config": config.config_path or "env/default",
    }


def identity_lines(config: EffectiveConfig) -> list[str]:
    config_label = config.config_path or "env/default"
    sources_display = ", ".join(config.sources) if config.sources else "none"
    secret_source = config.provenance.get("shared_secret", "missing")
    provenance_bits = [
        f"agent_id={config.provenance.get('agent_id', 'missing')}",
        f"shared_secret={secret_source}",
        f"endpoint={config.provenance.get('endpoint', 'missing')}",
    ]
    return [
        f"Config loaded from: {config_label}",
        f"Endpoint: {config.endpoint or 'missing'}",
        f"Agent ID: {config.agent_id or 'missing'}",
        f"Secret source: {secret_source}",
        f"Secret fingerprint: {secret_fingerprint(config.shared_secret or '')}",
        f"User: {_format_user()}",
        f"PID: {os.getpid()}",
        f"Sources: {sources_display}",
        f"Provenance: {', '.join(provenance_bits)}",
    ]
