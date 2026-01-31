from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml


def _default_config_path() -> Path:
    if os.name == "nt":
        program_data = Path(os.getenv("PROGRAMDATA", r"C:\ProgramData"))
        return program_data / "LogSentry" / "agent.yml"
    return Path("/etc/logsentry/agent.yml")


def _default_spool_path() -> Path:
    if os.name == "nt":
        program_data = Path(os.getenv("PROGRAMDATA", r"C:\ProgramData"))
        return program_data / "LogSentry" / "spool.db"
    return Path("/var/lib/logsentry/spool.db")


def _default_state_path() -> Path:
    if os.name == "nt":
        program_data = Path(os.getenv("PROGRAMDATA", r"C:\ProgramData"))
        return program_data / "LogSentry" / "state.json"
    return Path("/var/lib/logsentry/state.json")


DEFAULT_CONFIG_PATH = _default_config_path()

ENV_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")


def _expand_env_vars(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _expand_env_vars(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_expand_env_vars(item) for item in value]
    if not isinstance(value, str):
        return value

    def _replace(match: re.Match) -> str:
        token = match.group(1)
        if ":-" in token:
            var_name, default = token.split(":-", 1)
        else:
            var_name, default = token, None
        env_value = os.environ.get(var_name)
        if env_value is None:
            if default is None:
                raise ValueError(f"Missing environment variable: {var_name}")
            return default
        return env_value

    return ENV_VAR_PATTERN.sub(_replace, value)


@dataclass
class EffectiveConfig:
    agent_id: str | None
    shared_secret: str | None
    endpoint: str | None
    sources: list[str]
    config_path: str | None
    provenance: dict[str, str]


@dataclass
class AgentConfig:
    agent_id: str
    shared_secret: str
    shared_secret_file: Path | None
    endpoint: str
    log_dir: Path | None
    spool_path: Path
    spool_max_mb: int
    retry_max_seconds: int
    max_in_flight: int
    batch_size: int
    flush_interval_ms: int
    queue_max_size: int
    spool_drop_policy: str
    state_path: Path
    sources: list[str] = field(default_factory=list)
    allow_raw: bool = False
    privacy: "PrivacyConfig" | None = None
    security: "SecurityConfig" | None = None
    reliability: "ReliabilityConfig" | None = None
    health_interval_seconds: int = 60
    windows_noise_preset: str | None = None
    windows_eventlog: "WindowsEventLogConfig" | None = None
    nginx: "NginxConfig" | None = None
    apache: "ApacheConfig" | None = None
    ssh: "SshConfig" | None = None
    docker: "DockerConfig" | None = None


@dataclass
class PrivacyConfig:
    allow_raw: bool = False
    redact_patterns: list[str] = field(default_factory=list)
    field_redact_keys: list[str] = field(
        default_factory=lambda: [
            "authorization",
            "cookie",
            "set-cookie",
            "token",
            "password",
            "secret",
            "api_key",
        ]
    )
    max_event_bytes: int = 32768


@dataclass
class SecurityConfig:
    require_tls: bool = True
    allow_insecure_localhost_http: bool = True
    max_clock_skew_seconds: int = 300
    mtls_enabled: bool = False
    client_cert_path: Path | None = None
    client_key_path: Path | None = None
    ca_bundle_path: Path | None = None


@dataclass
class ReliabilityConfig:
    spool_drain_batch_size: int = 100
    spool_drain_interval_ms: int = 500
    spool_drain_percent: int | None = None
    drop_priority: list[str] = field(default_factory=lambda: ["raw", "low", "info"])
    spool_encrypt: bool = False
    spool_key_path: Path | None = None
    spool_on_queue_full: bool = False


@dataclass
class WindowsEventLogConfig:
    channels: list[str] = field(default_factory=lambda: ["Security", "System", "Application"])
    poll_interval_seconds: int = 2
    start_mode: str = "tail"
    since_minutes: int = 10
    from_record: int | None = None
    level_min: str = "Information"
    event_id_allow: list[int] = field(default_factory=list)
    event_id_deny: list[int] = field(default_factory=list)
    provider_allow: list[str] = field(default_factory=list)
    provider_deny: list[str] = field(default_factory=list)
    checkpoint_path: Path = field(default_factory=_default_state_path)
    max_events_per_poll: int = 200
    event_max_bytes: int = 32768
    redacted_fields: list[str] = field(
        default_factory=lambda: ["command_line", "sid", "token", "logon_guid"]
    )


@dataclass
class NginxConfig:
    access_log_paths: list[Path] = field(
        default_factory=lambda: [Path("/var/log/nginx/access.log")]
    )
    error_log_paths: list[Path] = field(default_factory=list)
    start_mode: str = "tail"
    since_minutes: int = 10
    max_line_bytes: int = 32768


@dataclass
class ApacheConfig:
    access_log_paths: list[Path] = field(
        default_factory=lambda: [
            Path("/var/log/apache2/access.log"),
            Path("/var/log/httpd/access_log"),
        ]
    )
    error_log_paths: list[Path] = field(default_factory=list)
    start_mode: str = "tail"
    since_minutes: int = 10
    max_line_bytes: int = 32768


@dataclass
class SshConfig:
    auth_log_paths: list[Path] = field(
        default_factory=lambda: [Path("/var/log/auth.log"), Path("/var/log/secure")]
    )
    start_mode: str = "tail"
    since_minutes: int = 10
    max_line_bytes: int = 32768


@dataclass
class DockerConfig:
    mode: str = "file"
    paths: list[Path] = field(default_factory=list)
    start_mode: str = "tail"
    since_minutes: int = 10
    max_line_bytes: int = 32768
    socket_path: Path | None = None


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return _expand_env_vars(data)


def _parse_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes", "on"}


def _normalize_for_hash(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: _normalize_for_hash(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_normalize_for_hash(item) for item in value]
    return value


def config_hash(config: AgentConfig) -> str:
    payload = _normalize_for_hash(asdict(config))
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _load_raw_configs(
    path: Path | None, *, allow_missing: bool = False
) -> tuple[Path | None, dict, dict]:
    config_path = path or DEFAULT_CONFIG_PATH
    if not config_path.exists():
        if allow_missing:
            return None, {}, _load_env_config()
        raise FileNotFoundError(f"Config file not found: {config_path}")
    return config_path, _load_yaml(config_path), _load_env_config()


def _load_env_config() -> dict[str, str | None]:
    return {
        "agent_id": os.getenv("LOGSENTRY_AGENT_ID"),
        "shared_secret": os.getenv("LOGSENTRY_AGENT_SECRET"),
        "shared_secret_file": os.getenv("LOGSENTRY_AGENT_SECRET_FILE"),
        "endpoint": os.getenv("LOGSENTRY_ENDPOINT"),
        "log_dir": os.getenv("LOGSENTRY_LOG_DIR"),
        "spool_path": os.getenv("LOGSENTRY_SPOOL_PATH"),
        "spool_max_mb": os.getenv("LOGSENTRY_SPOOL_MAX_MB"),
        "retry_max_seconds": os.getenv("LOGSENTRY_RETRY_MAX_SECONDS"),
        "max_in_flight": os.getenv("LOGSENTRY_MAX_IN_FLIGHT"),
        "batch_size": os.getenv("LOGSENTRY_BATCH_SIZE"),
        "flush_interval_ms": os.getenv("LOGSENTRY_FLUSH_INTERVAL_MS"),
        "queue_max_size": os.getenv("LOGSENTRY_QUEUE_MAX_SIZE"),
        "spool_drop_policy": os.getenv("LOGSENTRY_SPOOL_DROP_POLICY"),
        "state_path": os.getenv("LOGSENTRY_STATE_PATH"),
        "sources": os.getenv("LOGSENTRY_SOURCES"),
        "allow_raw": os.getenv("LOGSENTRY_ALLOW_RAW"),
        "privacy_allow_raw": os.getenv("LOGSENTRY_PRIVACY_ALLOW_RAW"),
    }


def load_effective_config(
    path: Path | None = None, *, allow_missing: bool = True
) -> EffectiveConfig:
    config_path, file_config, env_config = _load_raw_configs(path, allow_missing=allow_missing)

    def _resolve(key: str, default: Any = None) -> tuple[Any, str]:
        env_value = env_config.get(key)
        if env_value is not None:
            return env_value, "env"
        if key in file_config:
            return file_config.get(key), "file"
        if default is not None:
            return default, "default"
        return None, "missing"

    sources_value, sources_source = _resolve("sources", [])
    if isinstance(sources_value, str):
        sources_value = [item.strip() for item in sources_value.split(",") if item.strip()]

    agent_id, agent_id_source = _resolve("agent_id")
    endpoint, endpoint_source = _resolve("endpoint", "http://localhost:8002/v1/ingest")
    shared_secret, shared_secret_source = _resolve("shared_secret")
    shared_secret_file_raw, _shared_secret_file_source = _resolve("shared_secret_file")
    shared_secret_file = Path(shared_secret_file_raw) if shared_secret_file_raw else None
    if not shared_secret and shared_secret_file:
        if shared_secret_file.exists():
            shared_secret = shared_secret_file.read_text(encoding="utf-8").strip()
            shared_secret_source = "file"
        else:
            shared_secret_source = "missing"

    provenance = {
        "agent_id": agent_id_source,
        "shared_secret": shared_secret_source,
        "endpoint": endpoint_source,
        "sources": sources_source,
    }
    return EffectiveConfig(
        agent_id=agent_id,
        shared_secret=shared_secret,
        endpoint=endpoint,
        sources=sources_value,
        config_path=str(config_path) if config_path else None,
        provenance=provenance,
    )


def load_config(path: Path | None = None) -> AgentConfig:
    _, file_config, env_config = _load_raw_configs(path, allow_missing=False)

    def _get(key, default=None):
        value = env_config.get(key)
        if value is not None:
            return value
        return file_config.get(key, default)

    sources = _get("sources", [])
    if isinstance(sources, str):
        sources = [item.strip() for item in sources.split(",") if item.strip()]

    state_path_raw = _get("state_path")
    state_path_value = Path(state_path_raw) if state_path_raw else _default_state_path()
    log_dir_raw = _get("log_dir")
    log_dir_value = Path(log_dir_raw) if log_dir_raw else None
    windows_config = file_config.get("windows_eventlog", {}) or {}
    windows_noise_preset = file_config.get("windows_noise_preset")
    if windows_noise_preset and windows_noise_preset != "off":
        from logsentry_agent.presets.windows_noise import resolve_preset

        preset_config = resolve_preset(windows_noise_preset)
        for key, value in preset_config.items():
            if key not in windows_config or not windows_config.get(key):
                windows_config[key] = value
    if not state_path_raw and windows_config.get("checkpoint_path"):
        state_path_value = Path(windows_config["checkpoint_path"])
    checkpoint_path_value = windows_config.get("checkpoint_path", state_path_value)
    privacy_config = file_config.get("privacy", {}) or {}
    security_config = file_config.get("security", {}) or {}
    reliability_config = file_config.get("reliability", {}) or {}
    privacy_allow_raw = _get("privacy_allow_raw")
    if privacy_allow_raw is None:
        privacy_allow_raw = privacy_config.get("allow_raw")
    if privacy_allow_raw is None:
        privacy_allow_raw = _get("allow_raw", privacy_config.get("allow_raw", False))
    privacy = PrivacyConfig(
        allow_raw=_parse_bool(privacy_allow_raw, False),
        redact_patterns=privacy_config.get("redact_patterns", []),
        field_redact_keys=privacy_config.get(
            "field_redact_keys",
            ["authorization", "cookie", "set-cookie", "token", "password"],
        ),
        max_event_bytes=int(privacy_config.get("max_event_bytes", 32768)),
    )
    security = SecurityConfig(
        require_tls=_parse_bool(security_config.get("require_tls"), True),
        allow_insecure_localhost_http=_parse_bool(
            security_config.get("allow_insecure_localhost_http"), True
        ),
        max_clock_skew_seconds=int(security_config.get("max_clock_skew_seconds", 300)),
        mtls_enabled=_parse_bool(security_config.get("mtls_enabled"), False),
        client_cert_path=(
            Path(security_config["client_cert_path"])
            if security_config.get("client_cert_path")
            else None
        ),
        client_key_path=(
            Path(security_config["client_key_path"])
            if security_config.get("client_key_path")
            else None
        ),
        ca_bundle_path=(
            Path(security_config["ca_bundle_path"])
            if security_config.get("ca_bundle_path")
            else None
        ),
    )
    reliability = ReliabilityConfig(
        spool_drain_batch_size=int(reliability_config.get("spool_drain_batch_size", 100)),
        spool_drain_interval_ms=int(reliability_config.get("spool_drain_interval_ms", 500)),
        spool_drain_percent=(
            int(reliability_config["spool_drain_percent"])
            if reliability_config.get("spool_drain_percent") is not None
            else None
        ),
        drop_priority=reliability_config.get("drop_priority", ["raw", "low", "info"]),
        spool_encrypt=_parse_bool(reliability_config.get("spool_encrypt"), False),
        spool_key_path=(
            Path(reliability_config["spool_key_path"])
            if reliability_config.get("spool_key_path")
            else None
        ),
        spool_on_queue_full=_parse_bool(reliability_config.get("spool_on_queue_full"), False),
    )
    windows_eventlog = WindowsEventLogConfig(
        channels=windows_config.get("channels", ["Security", "System", "Application"]),
        poll_interval_seconds=int(windows_config.get("poll_interval_seconds", 2)),
        start_mode=windows_config.get("start_mode", "tail"),
        since_minutes=int(windows_config.get("since_minutes", 10)),
        from_record=(
            int(windows_config["from_record"]) if windows_config.get("from_record") else None
        ),
        level_min=windows_config.get("level_min", "Information"),
        event_id_allow=[int(item) for item in windows_config.get("event_id_allow", [])],
        event_id_deny=[int(item) for item in windows_config.get("event_id_deny", [])],
        provider_allow=windows_config.get("provider_allow", []),
        provider_deny=windows_config.get("provider_deny", []),
        checkpoint_path=Path(checkpoint_path_value),
        max_events_per_poll=int(windows_config.get("max_events_per_poll", 200)),
        event_max_bytes=int(windows_config.get("event_max_bytes", privacy.max_event_bytes)),
        redacted_fields=windows_config.get(
            "redacted_fields",
            ["command_line", "sid", "token", "logon_guid"],
        ),
    )
    nginx_config = file_config.get("nginx", {}) or {}
    apache_config = file_config.get("apache", {}) or {}
    ssh_config = file_config.get("ssh", {}) or {}
    docker_config = file_config.get("docker", {}) or {}

    nginx = NginxConfig(
        access_log_paths=[
            Path(item)
            for item in nginx_config.get("access_log_paths", NginxConfig().access_log_paths)
        ],
        error_log_paths=[Path(item) for item in nginx_config.get("error_log_paths", [])],
        start_mode=nginx_config.get("start_mode", "tail"),
        since_minutes=int(nginx_config.get("since_minutes", 10)),
        max_line_bytes=int(nginx_config.get("max_line_bytes", 32768)),
    )
    apache = ApacheConfig(
        access_log_paths=[
            Path(item)
            for item in apache_config.get("access_log_paths", ApacheConfig().access_log_paths)
        ],
        error_log_paths=[Path(item) for item in apache_config.get("error_log_paths", [])],
        start_mode=apache_config.get("start_mode", "tail"),
        since_minutes=int(apache_config.get("since_minutes", 10)),
        max_line_bytes=int(apache_config.get("max_line_bytes", 32768)),
    )
    ssh = SshConfig(
        auth_log_paths=[
            Path(item) for item in ssh_config.get("auth_log_paths", SshConfig().auth_log_paths)
        ],
        start_mode=ssh_config.get("start_mode", "tail"),
        since_minutes=int(ssh_config.get("since_minutes", 10)),
        max_line_bytes=int(ssh_config.get("max_line_bytes", 32768)),
    )
    docker = DockerConfig(
        mode=docker_config.get("mode", "file"),
        paths=[Path(item) for item in docker_config.get("paths", [])],
        start_mode=docker_config.get("start_mode", "tail"),
        since_minutes=int(docker_config.get("since_minutes", 10)),
        max_line_bytes=int(docker_config.get("max_line_bytes", 32768)),
        socket_path=(
            Path(docker_config["socket_path"]) if docker_config.get("socket_path") else None
        ),
    )

    shared_secret = _get("shared_secret")
    shared_secret_file_raw = _get("shared_secret_file")
    shared_secret_file = Path(shared_secret_file_raw) if shared_secret_file_raw else None
    if not shared_secret and shared_secret_file:
        if not shared_secret_file.exists():
            raise FileNotFoundError(f"shared_secret_file not found: {shared_secret_file}")
        shared_secret = shared_secret_file.read_text(encoding="utf-8").strip()

    return AgentConfig(
        agent_id=_get("agent_id"),
        shared_secret=shared_secret,
        shared_secret_file=shared_secret_file,
        endpoint=_get("endpoint", "http://localhost:8002/v1/ingest"),
        log_dir=log_dir_value,
        spool_path=Path(_get("spool_path", _default_spool_path())),
        spool_max_mb=int(_get("spool_max_mb", 64)),
        retry_max_seconds=int(_get("retry_max_seconds", 60)),
        max_in_flight=int(_get("max_in_flight", 200)),
        batch_size=int(_get("batch_size", 200)),
        flush_interval_ms=int(_get("flush_interval_ms", 2000)),
        queue_max_size=int(_get("queue_max_size", 1000)),
        spool_drop_policy=_get("spool_drop_policy", "drop_oldest"),
        state_path=state_path_value,
        sources=sources,
        allow_raw=_parse_bool(_get("allow_raw", privacy.allow_raw)),
        privacy=privacy,
        security=security,
        reliability=reliability,
        health_interval_seconds=int(file_config.get("health_interval_seconds", 60)),
        windows_noise_preset=windows_noise_preset,
        windows_eventlog=windows_eventlog,
        nginx=nginx,
        apache=apache,
        ssh=ssh,
        docker=docker,
    )
