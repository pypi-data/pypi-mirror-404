from pathlib import Path

from logsentry_agent.envelope import build_envelope
from logsentry_agent.state import AgentState


def test_envelope_sequence_persists(tmp_path: Path):
    state_path = tmp_path / "state.json"
    state = AgentState.load(state_path)
    seq1 = state.next_envelope_seq()
    state.save()
    seq2 = state.next_envelope_seq()
    state.save()

    assert seq1 == 1
    assert seq2 == 2

    reloaded = AgentState.load(state_path)
    assert reloaded.envelope_seq == 2


def test_envelope_contains_identity():
    envelope = build_envelope(version="0.1.3", events=[{"event_id": "1"}], seq=5)
    assert envelope["envelope"]["id"]
    assert envelope["envelope"]["seq"] == 5
    assert envelope["envelope"]["created_at"]
    assert envelope["schema_version"] == "v1"
    assert envelope["agent_time_utc"]
    assert envelope["agent_time_unix"]
