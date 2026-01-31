from __future__ import annotations

import hashlib
import json
import sqlite3
from base64 import urlsafe_b64encode
from pathlib import Path
from typing import Iterable

from cryptography.fernet import Fernet, InvalidToken


class SpoolQueue:
    def __init__(
        self,
        path: Path,
        max_mb: int,
        drop_policy: str = "drop_oldest",
        drop_priority: list[str] | None = None,
        encrypt: bool = False,
        encryption_key: str | None = None,
    ) -> None:
        self.path = path
        self.max_bytes = max_mb * 1024 * 1024
        self.drop_policy = drop_policy
        self.drop_priority = drop_priority or ["raw", "low", "info"]
        self._cipher = self._init_cipher(encrypt, encryption_key)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS spool (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payload TEXT NOT NULL,
                    priority TEXT DEFAULT 'low'
                )
                """
            )
            columns = [row[1] for row in conn.execute("PRAGMA table_info(spool)").fetchall()]
            if "priority" not in columns:
                conn.execute("ALTER TABLE spool ADD COLUMN priority TEXT DEFAULT 'low'")
            conn.commit()

    def _payload_size(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT SUM(LENGTH(payload)) FROM spool").fetchone()
        return int(row[0] or 0)

    def enqueue(self, payload: dict, *, priority: str = "low") -> bool:
        payload_text = json.dumps(payload, separators=(",", ":"))
        payload_text = self._encrypt(payload_text)
        if (
            self.drop_policy == "drop_newest"
            and self._payload_size() + len(payload_text.encode("utf-8")) > self.max_bytes
        ):
            return False
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO spool (payload, priority) VALUES (?, ?)",
                (payload_text, priority),
            )
            conn.commit()
        self._evict_if_needed()
        return True

    def dequeue_batch(self, limit: int) -> list[tuple[int, dict]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, payload FROM spool ORDER BY id ASC LIMIT ?",
                (limit,),
            ).fetchall()
        results = []
        for row_id, payload in rows:
            decrypted = self._decrypt(payload)
            if decrypted is None:
                continue
            results.append((row_id, json.loads(decrypted)))
        return results

    def delete(self, ids: list[int]) -> None:
        if not ids:
            return
        with self._connect() as conn:
            conn.executemany("DELETE FROM spool WHERE id = ?", [(row_id,) for row_id in ids])
            conn.commit()

    def pending_count(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) FROM spool").fetchone()
        return int(row[0]) if row else 0

    def _evict_if_needed(self) -> None:
        if self._payload_size() <= self.max_bytes or self.drop_policy == "drop_newest":
            return
        with self._connect() as conn:
            while self._payload_size() > self.max_bytes:
                if self.pending_count() == 0:
                    break
                deleted = self._evict_priority_batch(conn)
                if deleted == 0:
                    break

    def _evict_priority_batch(self, conn: sqlite3.Connection, batch_size: int = 100) -> int:
        for priority in self.drop_priority:
            ids = self._select_ids(conn, "priority = ?", (priority,), batch_size)
            if ids:
                self._delete_ids(conn, ids)
                return len(ids)
        ids = self._select_ids(conn, "1=1", tuple(), batch_size)
        if ids:
            self._delete_ids(conn, ids)
            return len(ids)
        return 0

    @staticmethod
    def _select_ids(
        conn: sqlite3.Connection, where: str, params: Iterable, limit: int
    ) -> list[int]:
        rows = conn.execute(
            f"SELECT id FROM spool WHERE {where} ORDER BY id ASC LIMIT ?",
            (*params, limit),
        ).fetchall()
        return [row[0] for row in rows]

    @staticmethod
    def _delete_ids(conn: sqlite3.Connection, ids: list[int]) -> None:
        conn.executemany("DELETE FROM spool WHERE id = ?", [(row_id,) for row_id in ids])
        conn.commit()

    @staticmethod
    def derive_key(shared_secret: str, *, salt: str = "logsentry-spool") -> str:
        digest = hashlib.sha256(f"{salt}:{shared_secret}".encode("utf-8")).digest()
        return urlsafe_b64encode(digest).decode("utf-8")

    def _init_cipher(self, encrypt: bool, encryption_key: str | None) -> Fernet | None:
        if not encrypt:
            return None
        if not encryption_key:
            raise ValueError("Spool encryption enabled but no encryption key provided.")
        key = encryption_key
        return Fernet(key)

    def _encrypt(self, payload_text: str) -> str:
        if not self._cipher:
            return payload_text
        return self._cipher.encrypt(payload_text.encode("utf-8")).decode("utf-8")

    def _decrypt(self, payload_text: str) -> str | None:
        if not self._cipher:
            return payload_text
        try:
            return self._cipher.decrypt(payload_text.encode("utf-8")).decode("utf-8")
        except InvalidToken:
            return None
