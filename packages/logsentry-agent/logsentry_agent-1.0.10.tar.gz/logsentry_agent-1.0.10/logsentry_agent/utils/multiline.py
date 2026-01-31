from __future__ import annotations

import re
import time
from dataclasses import dataclass, field

_START_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}[T\s]|\[\d{2}/[A-Za-z]{3}/\d{4}:|\{)")


@dataclass
class MultilineBuffer:
    timeout_seconds: float = 2.0
    _lines: list[str] = field(default_factory=list)
    _last_seen: float | None = None

    def feed(self, line: str, *, now: float | None = None) -> list[str]:
        current_time = now if now is not None else time.monotonic()
        completed: list[str] = []
        if self._last_seen is not None and self._lines:
            if current_time - self._last_seen >= self.timeout_seconds:
                completed.append("\n".join(self._lines))
                self._lines = []
        if self._is_start(line):
            if self._lines:
                completed.append("\n".join(self._lines))
            self._lines = [line]
        elif self._is_continuation(line) and self._lines:
            self._lines.append(line)
        else:
            if self._lines:
                completed.append("\n".join(self._lines))
            self._lines = [line]
        self._last_seen = current_time
        return completed

    def flush(self) -> str | None:
        if not self._lines:
            return None
        combined = "\n".join(self._lines)
        self._lines = []
        self._last_seen = None
        return combined

    @staticmethod
    def _is_start(line: str) -> bool:
        return bool(_START_RE.match(line))

    @staticmethod
    def _is_continuation(line: str) -> bool:
        stripped = line.lstrip()
        return line.startswith(" ") or stripped.startswith("at ") or stripped.startswith("...")
