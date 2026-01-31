from __future__ import annotations

import hashlib


def secret_fingerprint(secret: str) -> str:
    if not secret:
        return "missing"
    digest = hashlib.sha256(secret.encode("utf-8")).hexdigest()
    return digest[:10]
