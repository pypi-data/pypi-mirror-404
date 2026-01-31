from __future__ import annotations

from types import SimpleNamespace

from logsentry_agent.collectors import windows_eventlog
from logsentry_agent.config import WindowsEventLogConfig
from logsentry_agent.state import AgentState


def test_checkpoint_updates(tmp_path):
    state_path = tmp_path / "state.json"
    state = AgentState.load(state_path)
    state.update_checkpoint("Security", 120, "2024-01-01T00:00:00+00:00")
    state.save()

    reloaded = AgentState.load(state_path)
    assert reloaded.get_checkpoint("Security")["record_number"] == 120


def test_tail_start_mode_uses_latest_record(monkeypatch, tmp_path):
    fake_evtlog = SimpleNamespace(
        GetNumberOfEventLogRecords=lambda handle: 25,
        GetOldestEventLogRecord=lambda handle: 10,
    )
    monkeypatch.setattr(windows_eventlog, "win32evtlog", fake_evtlog)

    config = WindowsEventLogConfig(start_mode="tail")
    state = AgentState.load(tmp_path / "state.json")
    reader = windows_eventlog.WindowsEventLogReader(config, state)

    assert reader._determine_start_record("Security", object()) == 34
