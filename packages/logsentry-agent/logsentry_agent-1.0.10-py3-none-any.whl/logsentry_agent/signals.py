from __future__ import annotations

import signal
from dataclasses import dataclass


@dataclass
class ShutdownSignals:
    requested: bool = False

    def handler(self, signum: int, frame) -> None:  # noqa: ARG002
        self.requested = True


def install_signal_handlers() -> ShutdownSignals:
    shutdown = ShutdownSignals()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, shutdown.handler)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, shutdown.handler)
    return shutdown
