from logsentry_agent.utils.timeparse import parse_timestamp


def test_parse_common_formats():
    warnings: list[str] = []
    apache = "10/Oct/2000:13:55:36 -0700"
    iso = "2024-01-01T00:00:00+00:00"
    rfc = "2024-01-01T00:00:00Z"

    assert parse_timestamp(apache, warnings)
    assert parse_timestamp(iso, warnings) == "2024-01-01T00:00:00Z"
    assert parse_timestamp(rfc, warnings) == "2024-01-01T00:00:00Z"


def test_parse_syslog_format():
    warnings: list[str] = []
    assert parse_timestamp("Jan 20 13:00:00", warnings)
