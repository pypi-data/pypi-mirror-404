from logsentry_agent.normalize import apply_graceful_degradation


def test_derived_timestamp_sets_parse_confidence():
    event = {
        "source": "test",
        "category": "system",
        "action": "event.test",
        "severity": "low",
    }
    normalized = apply_graceful_degradation(event, parser="test_v1", confidence=1.0)
    assert normalized["timestamp_quality"] == "derived"
    assert normalized["parse"]["confidence"] < 1.0
    assert normalized["event_id"]
    assert normalized["schema_version"] == "v1"
    assert "host" in normalized
    assert "actor" in normalized
    assert "target" in normalized
