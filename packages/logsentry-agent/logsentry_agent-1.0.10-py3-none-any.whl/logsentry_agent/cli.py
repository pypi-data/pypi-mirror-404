from __future__ import annotations

import argparse
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

from logsentry_agent import __version__
from logsentry_agent.config import DEFAULT_CONFIG_PATH, load_config, load_effective_config
from logsentry_agent.envelope import build_envelope
from logsentry_agent.health import build_health_event
from logsentry_agent.http import SendResult, build_headers, send_payload
from logsentry_agent.identity import identity_exit_code, identity_lines
from logsentry_agent.run import _calculate_spool_drain_limit, _send_spool_payload, run_collectors
from logsentry_agent.spool import SpoolQueue
from logsentry_agent.state import AgentState


def _validate_credentials(config) -> str | None:
    missing = []
    if not config.agent_id:
        missing.append("agent_id")
    if not config.shared_secret:
        missing.append("shared_secret")
    if missing:
        return "Missing required agent configuration: " + ", ".join(missing)
    return None


def _load_spool_key(config) -> str | None:
    if not config.reliability or not config.reliability.spool_encrypt:
        return None
    if config.reliability.spool_key_path:
        return config.reliability.spool_key_path.read_text(encoding="utf-8").strip()
    return SpoolQueue.derive_key(config.shared_secret)


def _load_config_or_exit(config_path: Path | None):
    try:
        return load_config(config_path)
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc))
        raise SystemExit(1)


def _load_effective_config_or_exit(config_path: Path | None):
    try:
        return load_effective_config(config_path, allow_missing=True)
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc))
        raise SystemExit(1)


def _tls_requirement_ok(endpoint: str, security) -> bool:
    if not security or not security.require_tls:
        return True
    parsed = urlparse(endpoint)
    if parsed.scheme == "https":
        return True
    if (
        parsed.scheme == "http"
        and security.allow_insecure_localhost_http
        and parsed.hostname in {"localhost", "127.0.0.1"}
    ):
        return True
    return False


def _doctor_headers(agent_id: str, secret: str, body: bytes) -> dict[str, str]:
    timestamp = str(int(time.time()))
    nonce = f"{int.from_bytes(os.urandom(12), 'big'):024x}"
    return build_headers(
        agent_id=agent_id,
        secret=secret,
        body=body,
        nonce=nonce,
        timestamp=timestamp,
    )


def _print_counter_check(agent_id: str, response: requests.Response | None) -> None:
    print(f"Counter check — configured agent_id: {agent_id}")
    if response is None:
        print("Counter check — no backend response received.")
        return
    resolved_agent_id = response.headers.get("X-Resolved-Agent-Id")
    if not resolved_agent_id:
        print("Counter check — backend did not return X-Resolved-Agent-Id header.")
        return
    match_status = "match" if resolved_agent_id == agent_id else "mismatch"
    print(f"Counter check — backend resolved agent_id: {resolved_agent_id} ({match_status})")


def cmd_test_send(args: argparse.Namespace) -> int:
    config = _load_config_or_exit(args.config)
    spool = SpoolQueue(
        config.spool_path,
        config.spool_max_mb,
        config.spool_drop_policy,
        drop_priority=(config.reliability.drop_priority if config.reliability else None),
        encrypt=bool(config.reliability and config.reliability.spool_encrypt),
        encryption_key=_load_spool_key(config),
    )
    missing = _validate_credentials(config)
    if missing:
        print(missing)
        return 1
    event = {
        "source": "agent",
        "category": "system",
        "action": "test_send",
        "severity": "low",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": "LogSentry agent test event",
    }
    state = AgentState.load(config.state_path)
    payload = build_envelope(version=__version__, events=[event], seq=state.next_envelope_seq())
    state.save()
    result = send_payload(
        endpoint=config.endpoint,
        agent_id=config.agent_id,
        secret=config.shared_secret,
        payload=payload,
        retry_max_seconds=config.retry_max_seconds,
        security=config.security,
    )
    if getattr(args, "counter_check", False):
        _print_counter_check(config.agent_id, result.response)
    if result.status != "ok":
        spool.enqueue(payload, priority="low")
        status = result.response.status_code if result.response else "error"
        print(f"Backend rejected ({status}); event spooled.")
        return 1
    print("Test event accepted.")
    return 0


def cmd_send_health(args: argparse.Namespace) -> int:
    config = _load_config_or_exit(args.config)
    spool = SpoolQueue(
        config.spool_path,
        config.spool_max_mb,
        config.spool_drop_policy,
        drop_priority=(config.reliability.drop_priority if config.reliability else None),
        encrypt=bool(config.reliability and config.reliability.spool_encrypt),
        encryption_key=_load_spool_key(config),
    )
    missing = _validate_credentials(config)
    if missing:
        print(missing)
        return 1
    metrics = {
        "spool_size": spool.pending_count(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    state = AgentState.load(config.state_path)
    if state.stats.get("windows_eventlog"):
        metrics["windows_eventlog"] = state.stats["windows_eventlog"]
    payload = build_envelope(
        version=__version__, events=[build_health_event(metrics)], seq=state.next_envelope_seq()
    )
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
        spool.enqueue(payload, priority="low")
        return 1
    return 0


def cmd_drain_spool(args: argparse.Namespace) -> int:
    config = _load_config_or_exit(args.config)
    spool = SpoolQueue(
        config.spool_path,
        config.spool_max_mb,
        config.spool_drop_policy,
        drop_priority=(config.reliability.drop_priority if config.reliability else None),
        encrypt=bool(config.reliability and config.reliability.spool_encrypt),
        encryption_key=_load_spool_key(config),
    )
    missing = _validate_credentials(config)
    if missing:
        print(missing)
        return 1
    pending_count = spool.pending_count()
    if pending_count == 0:
        print("Spool empty.")
        return 0
    percent = args.percent
    if percent is None and config.reliability:
        percent = config.reliability.spool_drain_percent
    if percent is not None and (percent < 1 or percent > 100):
        print("Percent must be between 1 and 100.")
        return 2
    limit = _calculate_spool_drain_limit(
        pending_count=pending_count,
        config=config,
        batch_size_override=config.max_in_flight,
        percent_override=percent,
    )
    batch = spool.dequeue_batch(limit)
    ids_to_delete: list[int] = []
    last_result: SendResult | None = None
    for row_id, payload in batch:
        last_result, _, delete_row = _send_spool_payload(
            payload=payload,
            config=config,
            spool=spool,
        )
        if delete_row:
            ids_to_delete.append(row_id)
        if last_result and last_result.status != "ok":
            break
    spool.delete(ids_to_delete)
    if last_result and last_result.status != "ok":
        status = last_result.response.status_code if last_result.response else "error"
        print(f"Backend rejected ({status}); keeping spool.")
        return 1
    print("Spool drained.")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    config = _load_config_or_exit(args.config)
    issues = 0
    config_path = args.config if args.config else DEFAULT_CONFIG_PATH
    print(f"Config loaded from: {config_path}")
    missing = _validate_credentials(config)
    if missing:
        print(f"ERROR: {missing}")
        issues += 1
    if not _tls_requirement_ok(config.endpoint, config.security):
        print("ERROR: TLS is required for non-local endpoints.")
        issues += 1
    cert = None
    verify = (
        str(config.security.ca_bundle_path)
        if config.security and config.security.ca_bundle_path
        else True
    )
    if config.security and config.security.mtls_enabled:
        if not config.security.client_cert_path or not config.security.client_key_path:
            print("ERROR: mTLS enabled but client cert/key not set.")
            issues += 1
        else:
            cert = (
                str(config.security.client_cert_path),
                str(config.security.client_key_path),
            )
    body = b""
    headers = None
    if not missing:
        headers = _doctor_headers(config.agent_id, config.shared_secret, body)
    try:
        response = requests.head(
            config.endpoint,
            timeout=5,
            cert=cert,
            verify=verify,
            headers=headers,
        )
        print(f"Endpoint reachable: {response.status_code}")
        if getattr(args, "counter_check", False) and not missing:
            _print_counter_check(config.agent_id, response)
        if response.status_code in {401, 403}:
            print("WARNING: Endpoint rejected credentials.")
        elif response.status_code == 405:
            print("HEAD not allowed; authentication succeeded and POST is required.")
        elif response.status_code == 404:
            print("ERROR: Endpoint not found (404).")
            issues += 1
        elif response.status_code >= 500:
            print(f"ERROR: Endpoint returned server error ({response.status_code}).")
            issues += 1
    except requests.RequestException as exc:
        print(f"ERROR: Endpoint not reachable ({exc})")
        issues += 1
    return 1 if issues else 0


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _latest_poll(stats: dict) -> str | None:
    latest_time = None
    latest_raw = None
    for source, source_stats in stats.items():
        last_poll = source_stats.get("last_poll")
        parsed = _parse_timestamp(last_poll)
        if parsed is None:
            continue
        if latest_time is None or parsed > latest_time:
            latest_time = parsed
            latest_raw = last_poll
    return latest_raw


def cmd_status(args: argparse.Namespace) -> int:
    config = _load_config_or_exit(args.config)
    state = AgentState.load(config.state_path)
    agent_stats = state.stats.get("agent", {})
    uptime = agent_stats.get("uptime_seconds")
    last_send_status = agent_stats.get("last_send_status", "unknown")
    spool_depth = agent_stats.get("spool_depth", 0)
    last_poll = _latest_poll(state.stats)
    endpoint = state.audit.get("last_endpoint") or config.endpoint

    print(f"Endpoint: {endpoint}")
    print(f"Uptime (seconds): {uptime if uptime is not None else 'unknown'}")
    print(f"Last poll: {last_poll or 'unknown'}")
    print(f"Last send status: {last_send_status}")
    print(f"Spool depth: {spool_depth}")

    now = datetime.now(timezone.utc)
    last_poll_time = _parse_timestamp(last_poll)
    threshold_seconds = max(60, config.windows_eventlog.poll_interval_seconds * 5)
    if last_poll_time is None or (now - last_poll_time).total_seconds() > threshold_seconds:
        return 3
    if last_send_status and last_send_status != "ok":
        return 2
    return 0


def cmd_identity(args: argparse.Namespace) -> int:
    effective_config = _load_effective_config_or_exit(args.config)
    for line in identity_lines(effective_config):
        print(line)
    return identity_exit_code(effective_config)


def main() -> None:
    parser = argparse.ArgumentParser(description="LogSentry agent CLI")
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to agent.yml (defaults to system location).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"logsentry-agent {__version__}",
    )
    sub = parser.add_subparsers(dest="command")

    test_send_parser = sub.add_parser("test-send", help="Send a test event")
    test_send_parser.add_argument(
        "--counter-check",
        action="store_true",
        help="Display the configured agent_id and the backend-resolved agent_id, when available.",
    )
    sub.add_parser("send-health", help="Send a heartbeat event")
    drain_parser = sub.add_parser("drain-spool", help="Send queued events")
    drain_parser.add_argument(
        "--percent",
        type=int,
        help="Drain only this percentage of the current spool (1-100).",
    )
    run_parser = sub.add_parser("run", help="Run configured collectors")
    run_parser.add_argument("--once", action="store_true", help="Collect once and exit")
    run_parser.add_argument("--debug", action="store_true", help="Print collector stats")
    run_parser.add_argument(
        "--print-identity",
        action="store_true",
        help="Print identity details before running collectors.",
    )
    doctor_parser = sub.add_parser("doctor", help="Validate config and endpoint connectivity")
    doctor_parser.add_argument(
        "--counter-check",
        action="store_true",
        help="Display the configured agent_id and the backend-resolved agent_id, when available.",
    )
    sub.add_parser("identity", help="Print sanitized effective configuration identity")
    sub.add_parser("status", help="Show agent health from state.json")

    args = parser.parse_args()

    if args.command == "test-send":
        raise SystemExit(cmd_test_send(args))
    if args.command == "send-health":
        raise SystemExit(cmd_send_health(args))
    if args.command == "drain-spool":
        raise SystemExit(cmd_drain_spool(args))
    if args.command == "run":
        config = _load_config_or_exit(args.config)
        effective_config = _load_effective_config_or_exit(args.config)
        raise SystemExit(
            run_collectors(
                config=config,
                once=args.once,
                debug=args.debug,
                print_identity=args.print_identity,
                identity_config=effective_config,
            )
        )
    if args.command == "doctor":
        raise SystemExit(cmd_doctor(args))
    if args.command == "identity":
        raise SystemExit(cmd_identity(args))
    if args.command == "status":
        raise SystemExit(cmd_status(args))

    parser.print_help()


if __name__ == "__main__":
    main()
