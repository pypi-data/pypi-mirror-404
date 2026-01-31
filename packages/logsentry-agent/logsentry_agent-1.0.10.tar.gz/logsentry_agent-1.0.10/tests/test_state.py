import json
from pathlib import Path

from logsentry_agent.state import AgentState


def test_state_checksum_validation(tmp_path: Path):
    state_path = tmp_path / "state.json"
    state = AgentState.load(state_path)
    state.update_checkpoint("Security", 1, "2024-01-01T00:00:00+00:00")
    state.save()

    data = json.loads(state_path.read_text(encoding="utf-8"))
    data["checkpoints"]["Security"]["record_number"] = 999
    state_path.write_text(json.dumps(data), encoding="utf-8")

    loaded = AgentState.load(state_path)
    assert loaded.corrupted is True
    assert not state_path.exists()
    assert state_path.with_suffix(".json.corrupt").exists()
