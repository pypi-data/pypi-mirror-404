from pathlib import Path

from logsentry_agent.spool import SpoolQueue


def test_spool_enqueue_and_dequeue(tmp_path: Path):
    spool = SpoolQueue(tmp_path / "spool.db", max_mb=1)
    payload = {"events": [{"source": "test"}]}
    assert spool.enqueue(payload) is True

    batch = spool.dequeue_batch(10)
    assert len(batch) == 1
    row_id, stored = batch[0]
    assert stored == payload

    spool.delete([row_id])
    assert spool.pending_count() == 0


def test_spool_priority_eviction(tmp_path: Path):
    spool = SpoolQueue(tmp_path / "spool.db", max_mb=1, drop_priority=["low", "high"])
    large_payload = {"events": [{"message": "x" * 900_000}]}
    assert spool.enqueue(large_payload, priority="low") is True
    assert spool.enqueue(large_payload, priority="high") is True

    batch = spool.dequeue_batch(10)
    assert len(batch) == 1
    _, remaining = batch[0]
    assert remaining == large_payload


def test_spool_encrypts_payload(tmp_path: Path):
    key = SpoolQueue.derive_key("secret")
    spool = SpoolQueue(tmp_path / "spool.db", max_mb=1, encrypt=True, encryption_key=key)
    payload = {"events": [{"source": "test"}]}
    assert spool.enqueue(payload, priority="low") is True

    with spool._connect() as conn:
        row = conn.execute("SELECT payload FROM spool").fetchone()
    assert row is not None
    stored = row[0]
    assert "events" not in stored
