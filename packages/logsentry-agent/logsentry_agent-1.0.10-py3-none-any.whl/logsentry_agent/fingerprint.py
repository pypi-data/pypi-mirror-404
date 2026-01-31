from __future__ import annotations

import hashlib
import os
import platform
import socket


def _read_machine_id() -> str:
    for path in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    return handle.read().strip()
            except OSError:
                continue
    return ""


def compute_fingerprint() -> str:
    parts = [platform.system(), platform.release(), socket.gethostname(), _read_machine_id()]
    seed = "|".join(filter(None, parts))
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()
