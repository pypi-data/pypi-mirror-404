from __future__ import annotations

from pathlib import Path

from logsentry_agent.normalizers.windows_eventlog import normalize_event

from tests.helpers.deterministic_ids import patch_uuid4
from tests.helpers.golden import assert_events_match, load_expected, load_jsonl
from tests.helpers.host_patch import patch_hostname
from tests.helpers.time_patch import patch_time

FIXTURES = Path(__file__).parent / "fixtures" / "windows"


def test_windows_fixtures():
    with patch_hostname(), patch_time(), patch_uuid4("FIXTURE-WIN"):
        for fixture in sorted(FIXTURES.glob("*.input.jsonl")):
            events = [normalize_event(record) for record in load_jsonl(fixture)]
            events = [event for event in events if event is not None]
            expected = load_expected(fixture.with_suffix(fixture.suffix + ".expected.json"))
            assert_events_match(events, expected)
