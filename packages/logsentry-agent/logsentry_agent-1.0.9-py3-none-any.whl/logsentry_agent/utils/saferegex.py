from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SafeRegex:
    pattern: re.Pattern
    prefix: str | None = None

    def matches(self, text: str) -> re.Match | None:
        if self.prefix and self.prefix not in text:
            return None
        return self.pattern.search(text)


def compile_safe(pattern: str, *, flags: int = 0, prefix: str | None = None) -> SafeRegex:
    compiled = re.compile(pattern, flags)
    return SafeRegex(compiled, prefix=prefix)
