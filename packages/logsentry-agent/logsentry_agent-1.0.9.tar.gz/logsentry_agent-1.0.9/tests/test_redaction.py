from logsentry_agent.config import PrivacyConfig
from logsentry_agent.redact import redact_event


def test_redaction_by_key_and_pattern():
    privacy = PrivacyConfig(
        allow_raw=True,
        redact_patterns=[r"eyJ[^\s]+"],
        field_redact_keys=["authorization", "token"],
    )
    event = {
        "raw_line": "Authorization: Bearer eyJabc.def.ghi",
        "authorization": "Bearer secret",
        "message": "ok",
    }

    redacted = redact_event(event, privacy=privacy)
    assert redacted["authorization"] == "[REDACTED]"
    assert "[REDACTED]" in redacted["raw_line"]
    assert redacted["message"] == "ok"
