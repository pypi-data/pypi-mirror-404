from __future__ import annotations

from pathlib import Path

from logsentry_agent.collectors.docker import parse_line

from tests.helpers.deterministic_ids import patch_uuid4
from tests.helpers.golden import assert_events_match, load_expected, load_lines
from tests.helpers.host_patch import patch_hostname
from tests.helpers.time_patch import patch_time

FIXTURES = Path(__file__).parent / "fixtures" / "docker"


def _parse_fixture(path: Path) -> list[dict]:
    events: list[dict] = []
    enable_multiline = "multiline" in path.name
    for line in load_lines(path):
        parsed = parse_line(line, container="fixture-container", enable_multiline=enable_multiline)
        if isinstance(parsed, list):
            events.extend(parsed)
        elif parsed:
            events.append(parsed)
    if enable_multiline:
        flushed = parse_line(
            "",
            container="fixture-container",
            enable_multiline=True,
            flush=True,
        )
        if flushed:
            events.append(flushed)
    return events


def test_docker_fixtures():
    with patch_hostname(), patch_time(), patch_uuid4("FIXTURE-DKR"):
        for fixture in sorted(FIXTURES.glob("*.input.log")):
            events = _parse_fixture(fixture)
            expected = load_expected(fixture.with_suffix(fixture.suffix + ".expected.json"))
            assert_events_match(events, expected)
