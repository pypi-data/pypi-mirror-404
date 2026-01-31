from __future__ import annotations

from pathlib import Path

from logsentry_agent.collectors.nginx import parse_line

from tests.helpers.deterministic_ids import patch_uuid4
from tests.helpers.golden import assert_events_match, load_expected, load_lines
from tests.helpers.host_patch import patch_hostname
from tests.helpers.time_patch import patch_time

FIXTURES = Path(__file__).parent / "fixtures" / "nginx"


def test_nginx_fixtures():
    with patch_hostname(), patch_time(), patch_uuid4("FIXTURE-NGX"):
        for fixture in sorted(FIXTURES.glob("*.input.log")):
            events = [parse_line(line) for line in load_lines(fixture)]
            events = [event for event in events if event is not None]
            expected = load_expected(fixture.with_suffix(fixture.suffix + ".expected.json"))
            assert_events_match(events, expected)
