from __future__ import annotations

import hashlib
import hmac


def canonical_string(agent_id: str, timestamp: str, nonce: str, body_hash: str) -> str:
    return "\n".join([agent_id, timestamp, nonce, body_hash])


def compute_body_hash(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def sign_request(secret: str, agent_id: str, timestamp: str, nonce: str, body_hash: str) -> str:
    payload = canonical_string(agent_id, timestamp, nonce, body_hash)
    digest = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256)
    return digest.hexdigest()
