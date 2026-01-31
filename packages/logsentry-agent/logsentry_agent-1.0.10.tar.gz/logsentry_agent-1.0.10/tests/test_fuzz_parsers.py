from __future__ import annotations

import random
import string
from pathlib import Path

from logsentry_agent.collectors.apache import parse_line as parse_apache
from logsentry_agent.collectors.docker import parse_line as parse_docker
from logsentry_agent.collectors.nginx import parse_line as parse_nginx
from logsentry_agent.collectors.ssh import parse_line as parse_ssh

FIXTURES = Path(__file__).parent / "fixtures"


def _random_line(length: int) -> str:
    alphabet = string.ascii_letters + string.digits + "-_/[]{}:;,." * 2
    return "".join(random.choice(alphabet) for _ in range(length))


def test_parsers_handle_random_input():
    random.seed(42)
    for _ in range(500):
        line = _random_line(1024)
        assert parse_nginx(line) is None or isinstance(parse_nginx(line), dict)
        assert parse_apache(line) is None or isinstance(parse_apache(line), dict)
        assert parse_ssh(line) is None or isinstance(parse_ssh(line), dict)
        docker = parse_docker(line, container="fuzz")
        assert docker is None or isinstance(docker, (dict, list))


def test_nginx_long_path_fixture():
    weird_lines = (
        (FIXTURES / "nginx" / "weird_lines.input.log").read_text(encoding="utf-8").splitlines()
    )
    long_line = max(weird_lines, key=len)
    assert parse_nginx(long_line) is None or isinstance(parse_nginx(long_line), dict)
