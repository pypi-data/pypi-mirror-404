from __future__ import annotations

import errno
import json
import logging
import math
import os
import random
import sys
import time
from collections import deque
from datetime import datetime, timedelta, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse
from uuid import uuid4

from logsentry_agent import __version__
from logsentry_agent.collectors import parse_apache, parse_docker, parse_nginx, parse_ssh
from logsentry_agent.collectors.windows_eventlog import (
    WindowsEventLogReader,
    should_filter_since,
)
from logsentry_agent.config import AgentConfig, EffectiveConfig, PrivacyConfig, config_hash
from logsentry_agent.envelope import build_envelope, compute_priority
from logsentry_agent.health import build_health_event
from logsentry_agent.http import SendResult, send_payload
from logsentry_agent.identity import identity_exit_code, identity_lines, identity_summary
from logsentry_agent.normalize import apply_graceful_degradation
from logsentry_agent.normalizers.windows_eventlog import normalize_event
from logsentry_agent.redact import redact_event
from logsentry_agent.signals import install_signal_handlers
from logsentry_agent.spool import SpoolQueue
from logsentry_agent.state import AgentState


def _acquire_run_lock(lock_path: Path):
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_handle = lock_path.open("a+")
    try:
        if os.name == "nt":
            import msvcrt

            try:
                msvcrt.locking(lock_handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                lock_handle.close()
                return None
        else:
            import fcntl

            try:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                if exc.errno in (errno.EACCES, errno.EAGAIN):
                    lock_handle.close()
                    return None
                raise
    except Exception:
        lock_handle.close()
        raise
    return lock_handle


def _setup_logging(config: AgentConfig, *, debug: bool = False) -> logging.Logger:
    logger = logging.getLogger("logsentry_agent")
    if logger.handlers:
        logger.setLevel(logging.DEBUG if debug else logging.INFO)
        return logger
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
    formatter.converter = time.gmtime
    console = logging.StreamHandler(stream=sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)

    log_dir = config.log_dir
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_dir / "agent.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger


def _build_auth_failed_event(details: str) -> dict:
    event = {
        "source": "agent",
        "category": "security",
        "action": "agent.auth_failed",
        "severity": "high",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": details,
    }
    return apply_graceful_degradation(event, parser="agent_auth_failed_v1", confidence=1.0)


def _next_backoff(current: float, *, max_seconds: int, retry_after: float | None = None) -> float:
    if retry_after is not None:
        return min(retry_after, max_seconds)
    return max(1.0, min(current * 2 or 1.0, max_seconds))


def _load_spool_key(config: AgentConfig) -> str | None:
    if not config.reliability or not config.reliability.spool_encrypt:
        return None
    if config.reliability.spool_key_path:
        return config.reliability.spool_key_path.read_text(encoding="utf-8").strip()
    return SpoolQueue.derive_key(config.shared_secret)


def _update_agent_metrics(metrics: dict, *, start_time: float, spool: SpoolQueue) -> None:
    metrics["uptime_seconds"] = int(time.monotonic() - start_time)
    metrics["spool_depth"] = spool.pending_count()


def _record_send_result(metrics: dict, result: SendResult) -> None:
    metrics["last_send_status"] = result.status
    if result.status == "ok":
        metrics["last_successful_send"] = datetime.now(timezone.utc).isoformat()


def _apply_privacy_controls(
    event: dict,
    privacy: PrivacyConfig,
    stats: dict | None = None,
) -> dict:
    redacted = redact_event(event, privacy=privacy, stats=stats)
    if not privacy.allow_raw:
        redacted.pop("raw_line", None)
        redacted.pop("raw_event", None)
    return redacted


def _event_within_limit(event: dict, max_bytes: int) -> bool:
    payload_size = len(json.dumps(event, separators=(",", ":")).encode("utf-8"))
    return payload_size <= max_bytes


def _should_include_since(event: dict, since_minutes: int) -> bool:
    timestamp = event.get("timestamp")
    if not timestamp:
        return False
    try:
        parsed = datetime.fromisoformat(timestamp)
    except ValueError:
        return True
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed >= datetime.now(timezone.utc) - timedelta(minutes=since_minutes)


def _checkpoint_key(path: Path) -> str:
    return f"file:{path}"


def _read_file_lines(path: Path, *, state: AgentState, start_mode: str) -> tuple[list[str], bool]:
    try:
        stat = path.stat()
    except FileNotFoundError:
        return [], False
    size = stat.st_size
    inode = stat.st_ino
    checkpoint = state.get_checkpoint(_checkpoint_key(path))
    apply_since_filter = False
    if checkpoint and "offset" in checkpoint:
        offset = int(checkpoint["offset"])
        previous_inode = checkpoint.get("inode")
        if previous_inode and previous_inode != inode:
            offset = 0
        if offset > size:
            offset = 0
    else:
        if start_mode == "tail":
            offset = size
        else:
            offset = 0
            apply_since_filter = True
    lines: list[str] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        handle.seek(offset)
        for line in handle:
            lines.append(line.rstrip("\n"))
        offset = handle.tell()
    state.checkpoints[_checkpoint_key(path)] = {
        "offset": offset,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "inode": inode,
    }
    return lines, apply_since_filter


def _collect_file_events(
    *,
    paths: list[Path],
    state: AgentState,
    start_mode: str,
    since_minutes: int,
    max_line_bytes: int,
    parser: Callable[[str], dict | None],
) -> tuple[list[dict], dict]:
    events: list[dict] = []
    stats = {"parsed": 0, "unparsed": 0, "dropped": 0}
    for path in paths:
        lines, apply_since_filter = _read_file_lines(path, state=state, start_mode=start_mode)
        for line in lines:
            trimmed = line[:max_line_bytes] if max_line_bytes else line
            parsed = parser(trimmed)
            if not parsed:
                stats["dropped"] += 1
                continue
            parsed_events = parsed if isinstance(parsed, list) else [parsed]
            for event in parsed_events:
                if apply_since_filter and not _should_include_since(event, since_minutes):
                    continue
                events.append(event)
                confidence = float(event.get("parse", {}).get("confidence", 1.0))
                if confidence < 0.5:
                    stats["unparsed"] += 1
                else:
                    stats["parsed"] += 1
    return events, stats


def _collect_docker_events(
    *,
    paths: list[Path],
    state: AgentState,
    start_mode: str,
    since_minutes: int,
    max_line_bytes: int,
) -> tuple[list[dict], dict]:
    events: list[dict] = []
    stats = {"parsed": 0, "unparsed": 0, "dropped": 0}
    for path in paths:
        lines, apply_since_filter = _read_file_lines(path, state=state, start_mode=start_mode)
        container = path.parent.name or path.stem
        for line in lines:
            trimmed = line[:max_line_bytes] if max_line_bytes else line
            parsed = parse_docker(trimmed, container=container)
            if not parsed:
                stats["dropped"] += 1
                continue
            parsed_events = parsed if isinstance(parsed, list) else [parsed]
            for event in parsed_events:
                if apply_since_filter and not _should_include_since(event, since_minutes):
                    continue
                events.append(event)
                confidence = float(event.get("parse", {}).get("confidence", 1.0))
                if confidence < 0.5:
                    stats["unparsed"] += 1
                else:
                    stats["parsed"] += 1
    return events, stats


def _enqueue_event(
    *,
    event: dict,
    queue: deque[dict],
    agent_metrics: dict,
    config: AgentConfig,
    privacy: PrivacyConfig,
    count_event: bool = True,
    spool: SpoolQueue | None = None,
    state: AgentState | None = None,
    source_stats: dict | None = None,
) -> bool:
    sanitized = _apply_privacy_controls(event, privacy, stats=source_stats)
    if not _event_within_limit(sanitized, privacy.max_event_bytes):
        agent_metrics["events_dropped_total"] += 1
        agent_metrics["parse_failures"] += 1
        if source_stats is not None:
            source_stats["dropped"] = source_stats.get("dropped", 0) + 1
        return False
    if len(queue) < config.queue_max_size:
        queue.append(sanitized)
        if count_event:
            agent_metrics["events_collected_total"] += 1
        return True
    agent_metrics["events_dropped_total"] += 1
    agent_metrics["events_dropped_queue_full"] += 1
    if source_stats is not None:
        source_stats["dropped"] = source_stats.get("dropped", 0) + 1
    if (
        spool is not None
        and state is not None
        and config.reliability
        and config.reliability.spool_on_queue_full
    ):
        seq = state.next_envelope_seq()
        payload = build_envelope(version=__version__, events=[sanitized], seq=seq)
        state.save()
        priority = compute_priority(payload.get("events", []))
        if spool.enqueue(payload, priority=priority):
            agent_metrics["events_spooled_total"] += 1
            return True
    return False


def _handle_auth_failure(
    *,
    details: str,
    queue: deque[dict],
    agent_metrics: dict,
    config: AgentConfig,
    privacy: PrivacyConfig,
    spool: SpoolQueue,
    state: AgentState,
) -> None:
    auth_event = _build_auth_failed_event(details)
    _enqueue_event(
        event=auth_event,
        queue=queue,
        agent_metrics=agent_metrics,
        config=config,
        privacy=privacy,
        count_event=False,
        spool=spool,
        state=state,
    )
    health_event = build_health_event(agent_metrics, severity="high", details=details)
    _enqueue_event(
        event=health_event,
        queue=queue,
        agent_metrics=agent_metrics,
        config=config,
        privacy=privacy,
        count_event=False,
        spool=spool,
        state=state,
    )


def _drain_spool_batch(
    *,
    spool: SpoolQueue,
    config: AgentConfig,
    send_fn: Callable[..., SendResult] = send_payload,
) -> tuple[list[int], SendResult | None, int]:
    pending_count = spool.pending_count()
    limit = _calculate_spool_drain_limit(pending_count=pending_count, config=config)
    batch = spool.dequeue_batch(limit)
    ids_to_delete: list[int] = []
    last_result: SendResult | None = None
    sent_events = 0
    for row_id, payload in batch:
        last_result, sent, delete_row = _send_spool_payload(
            payload=payload,
            config=config,
            spool=spool,
            send_fn=send_fn,
        )
        sent_events += sent
        if delete_row:
            ids_to_delete.append(row_id)
        if last_result and last_result.status != "ok":
            break
    spool.delete(ids_to_delete)
    return ids_to_delete, last_result, sent_events


def _send_spool_payload(
    *,
    payload: dict,
    config: AgentConfig,
    spool: SpoolQueue,
    send_fn: Callable[..., SendResult] = send_payload,
) -> tuple[SendResult | None, int, bool]:
    result = send_fn(
        endpoint=config.endpoint,
        agent_id=config.agent_id,
        secret=config.shared_secret,
        payload=payload,
        retry_max_seconds=config.retry_max_seconds,
        security=config.security,
    )
    if result.status == "ok":
        return result, len(payload.get("events", [])), True
    if result.response is not None and result.response.status_code == 400:
        return _send_spool_payload_individually(
            payload=payload,
            config=config,
            spool=spool,
            send_fn=send_fn,
        )
    return result, 0, False


def _send_spool_payload_individually(
    *,
    payload: dict,
    config: AgentConfig,
    spool: SpoolQueue,
    send_fn: Callable[..., SendResult] = send_payload,
) -> tuple[SendResult | None, int, bool]:
    events = payload.get("events", []) if isinstance(payload, dict) else []
    if not events:
        return SendResult(status="ok"), 0, True
    sent_events = 0
    last_result: SendResult | None = None
    for index, event in enumerate(events):
        single_payload = _build_single_event_payload(payload, event)
        last_result = send_fn(
            endpoint=config.endpoint,
            agent_id=config.agent_id,
            secret=config.shared_secret,
            payload=single_payload,
            retry_max_seconds=config.retry_max_seconds,
            security=config.security,
        )
        if last_result.status == "ok":
            sent_events += 1
            continue
        status_code = last_result.response.status_code if last_result.response is not None else None
        if status_code == 400:
            continue
        remaining = [event, *events[index + 1 :]]
        for pending in remaining:
            pending_payload = _build_single_event_payload(payload, pending)
            priority = compute_priority(pending_payload.get("events", []))
            spool.enqueue(pending_payload, priority=priority)
        return last_result, sent_events, True
    return (
        SendResult(status="ok", response=last_result.response if last_result else None),
        sent_events,
        True,
    )


def _build_single_event_payload(payload: dict, event: dict) -> dict:
    envelope = dict(payload.get("envelope") or {}) if isinstance(payload, dict) else {}
    envelope["id"] = str(uuid4())
    return {
        **payload,
        "envelope": envelope,
        "events": [event],
    }


def _calculate_spool_drain_limit(
    *,
    pending_count: int,
    config: AgentConfig,
    batch_size_override: int | None = None,
    percent_override: int | None = None,
) -> int:
    batch_size = batch_size_override or (
        config.reliability.spool_drain_batch_size if config.reliability else 100
    )
    percent = (
        percent_override
        if percent_override is not None
        else (config.reliability.spool_drain_percent if config.reliability else None)
    )
    if percent is None or percent <= 0:
        return batch_size
    percent = min(percent, 100)
    percent_limit = max(1, math.ceil(pending_count * (percent / 100)))
    return min(batch_size, percent_limit)


def run_collectors(
    *,
    config: AgentConfig,
    once: bool = False,
    debug: bool = False,
    print_identity: bool = False,
    identity_config: EffectiveConfig | None = None,
) -> int:
    logger = _setup_logging(config, debug=debug)
    if print_identity and identity_config:
        for line in identity_lines(identity_config):
            print(line)
        if once:
            return identity_exit_code(identity_config)
    if debug and identity_config:
        summary = identity_summary(identity_config)
        logger.debug(
            "identity agent_id=%s endpoint=%s secret_fp=%s secret_src=%s config=%s",
            summary["agent_id"],
            summary["endpoint"],
            summary["secret_fp"],
            summary["secret_src"],
            summary["config"],
        )
    lock_path = config.state_path.with_suffix(".lock")
    _lock_handle = _acquire_run_lock(lock_path)
    if _lock_handle is None:
        logger.info("Another logsentry-agent instance is already running (%s).", lock_path)
        return 0

    state = AgentState.load(config.state_path)
    spool_key = _load_spool_key(config)
    spool = SpoolQueue(
        config.spool_path,
        config.spool_max_mb,
        config.spool_drop_policy,
        drop_priority=(config.reliability.drop_priority if config.reliability else None),
        encrypt=bool(config.reliability and config.reliability.spool_encrypt),
        encryption_key=spool_key,
    )
    if not config.agent_id or not config.shared_secret:
        logger.error("Missing required agent configuration: agent_id, shared_secret")
        return 1
    parsed_endpoint = urlparse(config.endpoint)
    if not parsed_endpoint.scheme or not parsed_endpoint.netloc:
        logger.error("Invalid endpoint URL format: %s", config.endpoint)
        return 1

    privacy = config.privacy or PrivacyConfig(allow_raw=config.allow_raw)
    sources = {source.lower() for source in config.sources}

    windows_collector = None
    if "windows_eventlog" in sources or "windows" in sources:
        windows_collector = WindowsEventLogReader(config.windows_eventlog, state)
    linux_sources = {"nginx", "apache", "ssh", "docker"} & sources
    if windows_collector is None and not linux_sources:
        logger.error(
            "No supported collectors configured. Add `windows_eventlog` or Linux sources to "
            "sources."
        )
        return 1

    state.audit.update(
        {
            "last_agent_version": __version__,
            "last_endpoint": config.endpoint,
            "last_config_hash": config_hash(config),
        }
    )
    state.save()

    queue: deque[dict] = deque()
    backoff_seconds = 0.0
    next_send_time = 0.0
    last_flush = time.monotonic()
    last_spool_drain = time.monotonic()
    last_health = time.monotonic()
    send_enabled = True
    auth_pause_until = 0.0
    start_time = time.monotonic()

    agent_metrics = state.stats.get("agent", {})
    agent_metrics.setdefault("events_collected_total", 0)
    agent_metrics.setdefault("events_sent_total", 0)
    agent_metrics.setdefault("events_spooled_total", 0)
    agent_metrics.setdefault("events_dropped_total", 0)
    agent_metrics.setdefault("events_dropped_queue_full", 0)
    agent_metrics.setdefault("parse_failures", 0)
    if state.corrupted:
        agent_metrics["state_corrupt"] = True

    health_interval = config.health_interval_seconds
    _enqueue_event(
        event=build_health_event(agent_metrics),
        queue=queue,
        agent_metrics=agent_metrics,
        config=config,
        privacy=privacy,
        count_event=False,
        spool=spool,
        state=state,
    )

    shutdown = install_signal_handlers()

    while True:
        poll_start = time.monotonic()
        if not send_enabled and auth_pause_until:
            now = time.monotonic()
            if now < auth_pause_until:
                time.sleep(auth_pause_until - now)
                continue
            send_enabled = True
            auth_pause_until = 0.0
        if windows_collector:
            try:
                records, stats = windows_collector.poll()
            except RuntimeError as exc:
                logger.error("%s", exc)
                return 1
            windows_stats = {"parsed": 0, "unparsed": 0, "dropped": 0, "redacted_count": 0}
            for record in records:
                if (
                    config.windows_eventlog.start_mode == "since_minutes"
                    and not state.get_checkpoint(record["channel"])
                ):
                    if should_filter_since(record, config.windows_eventlog.since_minutes):
                        continue
                normalized = normalize_event(
                    record,
                    allow_raw=privacy.allow_raw,
                    redacted_fields=set(config.windows_eventlog.redacted_fields),
                    event_max_bytes=config.windows_eventlog.event_max_bytes,
                )
                if normalized is None:
                    stats.dropped_too_large += 1
                    agent_metrics["events_dropped_total"] += 1
                    agent_metrics["parse_failures"] += 1
                    windows_stats["dropped"] += 1
                    continue
                confidence = float(normalized.get("parse", {}).get("confidence", 1.0))
                if confidence < 0.5:
                    windows_stats["unparsed"] += 1
                else:
                    windows_stats["parsed"] += 1
                _enqueue_event(
                    event=normalized,
                    queue=queue,
                    agent_metrics=agent_metrics,
                    config=config,
                    privacy=privacy,
                    spool=spool,
                    state=state,
                    source_stats=windows_stats,
                )
            state.update_stats(
                "windows_eventlog",
                {
                    "events_collected_last_poll": stats.events_collected,
                    "access_denied": stats.access_denied,
                    "dropped_too_large": stats.dropped_too_large,
                    "last_bookmarks": stats.last_bookmarks,
                    "last_poll": datetime.now(timezone.utc).isoformat(),
                    "spool_size": spool.pending_count(),
                    **windows_stats,
                },
            )
            _update_agent_metrics(agent_metrics, start_time=start_time, spool=spool)
            state.update_stats("agent", agent_metrics)
            state.save()
            if debug:
                logger.debug(
                    "Windows collector stats: %s",
                    {
                        "events_collected": stats.events_collected,
                        "last_bookmarks": stats.last_bookmarks,
                        "access_denied": stats.access_denied,
                        "queue_size": len(queue),
                        "spool_size": spool.pending_count(),
                    },
                )

        if os.name != "nt" and linux_sources:
            linux_stats: dict[str, dict] = {}
            if "nginx" in linux_sources:
                events, parse_stats = _collect_file_events(
                    paths=config.nginx.access_log_paths + config.nginx.error_log_paths,
                    state=state,
                    start_mode=config.nginx.start_mode,
                    since_minutes=config.nginx.since_minutes,
                    max_line_bytes=config.nginx.max_line_bytes,
                    parser=parse_nginx,
                )
                linux_stats["nginx"] = {
                    "events_collected_last_poll": len(events),
                    "last_poll": datetime.now(timezone.utc).isoformat(),
                    "parsed": parse_stats["parsed"],
                    "unparsed": parse_stats["unparsed"],
                    "dropped": parse_stats["dropped"],
                    "redacted_count": 0,
                }
                for event in events:
                    _enqueue_event(
                        event=event,
                        queue=queue,
                        agent_metrics=agent_metrics,
                        config=config,
                        privacy=privacy,
                        spool=spool,
                        state=state,
                        source_stats=linux_stats["nginx"],
                    )
            if "apache" in linux_sources:
                events, parse_stats = _collect_file_events(
                    paths=config.apache.access_log_paths + config.apache.error_log_paths,
                    state=state,
                    start_mode=config.apache.start_mode,
                    since_minutes=config.apache.since_minutes,
                    max_line_bytes=config.apache.max_line_bytes,
                    parser=parse_apache,
                )
                linux_stats["apache"] = {
                    "events_collected_last_poll": len(events),
                    "last_poll": datetime.now(timezone.utc).isoformat(),
                    "parsed": parse_stats["parsed"],
                    "unparsed": parse_stats["unparsed"],
                    "dropped": parse_stats["dropped"],
                    "redacted_count": 0,
                }
                for event in events:
                    _enqueue_event(
                        event=event,
                        queue=queue,
                        agent_metrics=agent_metrics,
                        config=config,
                        privacy=privacy,
                        spool=spool,
                        state=state,
                        source_stats=linux_stats["apache"],
                    )
            if "ssh" in linux_sources:
                events, parse_stats = _collect_file_events(
                    paths=config.ssh.auth_log_paths,
                    state=state,
                    start_mode=config.ssh.start_mode,
                    since_minutes=config.ssh.since_minutes,
                    max_line_bytes=config.ssh.max_line_bytes,
                    parser=parse_ssh,
                )
                linux_stats["ssh"] = {
                    "events_collected_last_poll": len(events),
                    "last_poll": datetime.now(timezone.utc).isoformat(),
                    "parsed": parse_stats["parsed"],
                    "unparsed": parse_stats["unparsed"],
                    "dropped": parse_stats["dropped"],
                    "redacted_count": 0,
                }
                for event in events:
                    _enqueue_event(
                        event=event,
                        queue=queue,
                        agent_metrics=agent_metrics,
                        config=config,
                        privacy=privacy,
                        spool=spool,
                        state=state,
                        source_stats=linux_stats["ssh"],
                    )
            if "docker" in linux_sources and config.docker.mode == "file":
                events, parse_stats = _collect_docker_events(
                    paths=config.docker.paths,
                    state=state,
                    start_mode=config.docker.start_mode,
                    since_minutes=config.docker.since_minutes,
                    max_line_bytes=config.docker.max_line_bytes,
                )
                linux_stats["docker"] = {
                    "events_collected_last_poll": len(events),
                    "last_poll": datetime.now(timezone.utc).isoformat(),
                    "parsed": parse_stats["parsed"],
                    "unparsed": parse_stats["unparsed"],
                    "dropped": parse_stats["dropped"],
                    "redacted_count": 0,
                }
                for event in events:
                    _enqueue_event(
                        event=event,
                        queue=queue,
                        agent_metrics=agent_metrics,
                        config=config,
                        privacy=privacy,
                        spool=spool,
                        state=state,
                        source_stats=linux_stats["docker"],
                    )
            for source_name, stats in linux_stats.items():
                state.update_stats(source_name, stats)
            if linux_stats:
                _update_agent_metrics(agent_metrics, start_time=start_time, spool=spool)
                state.update_stats("agent", agent_metrics)
                state.save()

        if health_interval and (time.monotonic() - last_health) >= health_interval:
            _update_agent_metrics(agent_metrics, start_time=start_time, spool=spool)
            health_event = build_health_event(agent_metrics)
            _enqueue_event(
                event=health_event,
                queue=queue,
                agent_metrics=agent_metrics,
                config=config,
                privacy=privacy,
                count_event=False,
                spool=spool,
                state=state,
            )
            last_health = time.monotonic()

        can_send = send_enabled and time.monotonic() >= next_send_time
        if (
            can_send
            and spool.pending_count() > 0
            and (time.monotonic() - last_spool_drain) * 1000
            >= (config.reliability.spool_drain_interval_ms if config.reliability else 1000)
        ):
            ids_to_delete, result, sent_events = _drain_spool_batch(
                spool=spool,
                config=config,
            )
            if result:
                _record_send_result(agent_metrics, result)
            agent_metrics["events_sent_total"] += sent_events
            if result and result.auth_failed:
                send_enabled = False
                auth_pause_until = time.monotonic() + config.retry_max_seconds
                logger.warning("Authentication failed; pausing sends for retry window.")
                _handle_auth_failure(
                    details=result.error or "auth failed",
                    queue=queue,
                    agent_metrics=agent_metrics,
                    config=config,
                    privacy=privacy,
                    spool=spool,
                    state=state,
                )
            elif result and result.status != "ok":
                logger.warning(
                    "Spool drain send failed (%s). Backing off.",
                    result.status if result else "unknown",
                )
                backoff_seconds = _next_backoff(
                    backoff_seconds,
                    max_seconds=config.retry_max_seconds,
                    retry_after=result.retry_after_seconds,
                )
                next_send_time = (
                    time.monotonic()
                    + backoff_seconds
                    + (0.0 if result.retry_after_seconds else random.random())
                )
            last_spool_drain = time.monotonic()

        batch_limit = min(config.batch_size, config.max_in_flight)
        should_flush = (
            len(queue) >= batch_limit
            or (time.monotonic() - last_flush) * 1000 >= config.flush_interval_ms
        )
        if queue and should_flush:
            if send_enabled and time.monotonic() < next_send_time:
                pass
            else:
                batch = [queue.popleft() for _ in range(min(batch_limit, len(queue)))]
                seq = state.next_envelope_seq()
                payload = build_envelope(version=__version__, events=batch, seq=seq)
                state.save()
                if send_enabled:
                    result = send_payload(
                        endpoint=config.endpoint,
                        agent_id=config.agent_id,
                        secret=config.shared_secret,
                        payload=payload,
                        retry_max_seconds=config.retry_max_seconds,
                        security=config.security,
                    )
                    _record_send_result(agent_metrics, result)
                else:
                    result = SendResult(status="fatal", error="auth_failed", auth_failed=True)
                if result.status == "ok":
                    agent_metrics["events_sent_total"] += len(batch)
                    backoff_seconds = 0.0
                    next_send_time = 0.0
                elif result.auth_failed:
                    send_enabled = False
                    auth_pause_until = time.monotonic() + config.retry_max_seconds
                    logger.warning("Authentication failed; pausing sends for retry window.")
                    _handle_auth_failure(
                        details=result.error or "auth failed",
                        queue=queue,
                        agent_metrics=agent_metrics,
                        config=config,
                        privacy=privacy,
                        spool=spool,
                        state=state,
                    )
                    agent_metrics["events_dropped_total"] += len(batch)
                else:
                    if result.status == "fatal":
                        logger.error(
                            "Send returned fatal status; continuing with backoff: %s",
                            result.error or "unknown",
                        )
                    priority = compute_priority(payload.get("events", []))
                    if spool.enqueue(payload, priority=priority):
                        agent_metrics["events_spooled_total"] += len(batch)
                    else:
                        agent_metrics["events_dropped_total"] += len(batch)
                    backoff_seconds = _next_backoff(
                        backoff_seconds,
                        max_seconds=config.retry_max_seconds,
                        retry_after=result.retry_after_seconds,
                    )
                    next_send_time = (
                        time.monotonic()
                        + backoff_seconds
                        + (0.0 if result.retry_after_seconds else random.random())
                    )
                _update_agent_metrics(agent_metrics, start_time=start_time, spool=spool)
                state.update_stats("agent", agent_metrics)
                state.save()
                last_flush = time.monotonic()

        if shutdown.requested:
            break
        if once:
            break
        elapsed = time.monotonic() - poll_start
        sleep_for = max(config.windows_eventlog.poll_interval_seconds - elapsed, 0.0)
        time.sleep(sleep_for)

    _update_agent_metrics(agent_metrics, start_time=start_time, spool=spool)
    shutdown_event = build_health_event(agent_metrics)
    _enqueue_event(
        event=shutdown_event,
        queue=queue,
        agent_metrics=agent_metrics,
        config=config,
        privacy=privacy,
        count_event=False,
        spool=spool,
        state=state,
    )
    while queue:
        batch = list(queue)
        queue.clear()
        seq = state.next_envelope_seq()
        payload = build_envelope(version=__version__, events=batch, seq=seq)
        state.save()
        result = send_payload(
            endpoint=config.endpoint,
            agent_id=config.agent_id,
            secret=config.shared_secret,
            payload=payload,
            retry_max_seconds=config.retry_max_seconds,
            security=config.security,
        )
        if result.status != "ok":
            priority = compute_priority(payload.get("events", []))
            spool.enqueue(payload, priority=priority)
            return 1
        agent_metrics["events_sent_total"] += len(batch)

    state.update_stats("agent", agent_metrics)
    state.save()
    return 0
