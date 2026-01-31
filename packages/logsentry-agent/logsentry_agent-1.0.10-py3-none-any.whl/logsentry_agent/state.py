from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AgentState:
    path: Path
    checkpoints: dict[str, dict] = field(default_factory=dict)
    stats: dict[str, dict] = field(default_factory=dict)
    envelope_seq: int = 0
    audit: dict[str, str] = field(default_factory=dict)
    corrupted: bool = False

    def _payload(self) -> dict[str, Any]:
        return {
            "checkpoints": self.checkpoints,
            "stats": self.stats,
            "envelope_seq": self.envelope_seq,
            "audit": self.audit,
        }

    @staticmethod
    def _checksum(data: dict[str, Any]) -> str:
        return hashlib.sha256(
            json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = self._payload()
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(
                {
                    **payload,
                    "_meta": {
                        "schema_version": "v1",
                        "checksum": self._checksum(payload),
                    },
                },
                handle,
            )

    @classmethod
    def load(cls, path: Path) -> "AgentState":
        if not path.exists():
            return cls(path=path)
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        meta = data.get("_meta", {})
        payload = {
            "checkpoints": data.get("checkpoints", {}),
            "stats": data.get("stats", {}),
            "envelope_seq": int(data.get("envelope_seq", 0)),
            "audit": data.get("audit", {}),
        }
        if meta:
            expected = meta.get("checksum")
            actual = cls._checksum(payload)
            if expected and expected != actual:
                corrupted_path = path.with_suffix(path.suffix + ".corrupt")
                shutil.move(path, corrupted_path)
                return cls(path=path, corrupted=True)
        return cls(
            path=path,
            checkpoints=payload["checkpoints"],
            stats=payload["stats"],
            envelope_seq=payload["envelope_seq"],
            audit=payload["audit"],
        )

    def update_checkpoint(self, channel: str, record_number: int, timestamp: str) -> None:
        self.checkpoints[channel] = {
            "record_number": record_number,
            "timestamp": timestamp,
        }

    def get_checkpoint(self, channel: str) -> dict | None:
        return self.checkpoints.get(channel)

    def update_stats(self, key: str, value: dict) -> None:
        self.stats[key] = value

    def next_envelope_seq(self) -> int:
        self.envelope_seq += 1
        return self.envelope_seq
