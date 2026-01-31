from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlparse

import requests

from logsentry_agent.config import SecurityConfig
from logsentry_agent.signer import compute_body_hash, sign_request


def build_headers(*, agent_id: str, secret: str, body: bytes, nonce: str, timestamp: str) -> dict:
    body_hash = compute_body_hash(body)
    signature = sign_request(secret, agent_id, timestamp, nonce, body_hash)
    return {
        "X-Agent-Id": agent_id,
        "X-Agent-Timestamp": timestamp,
        "X-Agent-Nonce": nonce,
        "X-Agent-Signature": signature,
        "X-Agent-Content-SHA256": body_hash,
        "Content-Type": "application/json",
    }


@dataclass
class SendResult:
    status: str
    response: requests.Response | None = None
    retry_after_seconds: float | None = None
    error: str | None = None
    auth_failed: bool = False


def _parse_retry_after(response: requests.Response) -> float | None:
    header = response.headers.get("Retry-After")
    if not header:
        return None
    try:
        return float(header)
    except ValueError:
        try:
            parsed = parsedate_to_datetime(header)
        except (TypeError, ValueError):
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        delta = parsed - datetime.now(timezone.utc)
        return max(delta.total_seconds(), 0.0)


def _is_tls_required(endpoint: str, security: SecurityConfig) -> bool:
    parsed = urlparse(endpoint)
    if parsed.scheme == "https":
        return False
    if (
        parsed.scheme == "http"
        and security.allow_insecure_localhost_http
        and parsed.hostname in {"localhost", "127.0.0.1"}
    ):
        return False
    return True


def send_payload(
    *,
    endpoint: str,
    agent_id: str,
    secret: str,
    payload: dict[str, Any],
    retry_max_seconds: int,
    security: SecurityConfig | None = None,
) -> SendResult:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    if security and security.require_tls and _is_tls_required(endpoint, security):
        return SendResult(status="fatal", error="TLS required for non-local endpoints.")
    cert = None
    verify = str(security.ca_bundle_path) if security and security.ca_bundle_path else True
    if security and security.mtls_enabled:
        if not security.client_cert_path or not security.client_key_path:
            return SendResult(status="fatal", error="mTLS enabled but client cert/key not set.")
        cert = (str(security.client_cert_path), str(security.client_key_path))
    timestamp = str(int(time.time()))
    nonce = f"{int.from_bytes(os.urandom(12), 'big'):024x}"
    headers = build_headers(
        agent_id=agent_id,
        secret=secret,
        body=body,
        nonce=nonce,
        timestamp=timestamp,
    )
    try:
        response = requests.post(
            endpoint, data=body, headers=headers, timeout=10, cert=cert, verify=verify
        )
    except requests.RequestException as exc:
        return SendResult(status="retry", error=str(exc))
    if 200 <= response.status_code < 300:
        return SendResult(status="ok", response=response)
    if response.status_code == 429:
        retry_after = _parse_retry_after(response)
        return SendResult(status="retry", response=response, retry_after_seconds=retry_after)
    if response.status_code in {401, 403}:
        return SendResult(status="fatal", response=response, auth_failed=True)
    if response.status_code >= 500:
        return SendResult(status="retry", response=response)
    return SendResult(status="retry", response=response)
