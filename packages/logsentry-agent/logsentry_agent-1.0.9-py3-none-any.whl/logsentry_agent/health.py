from __future__ import annotations

from datetime import datetime, timezone

from logsentry_agent.normalize import apply_graceful_degradation


def build_health_event(metrics: dict, *, severity: str = "low", details: str | None = None) -> dict:
    event = {
        "source": "agent",
        "category": "system",
        "action": "agent.health",
        "severity": severity,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
    }
    if details:
        event["details"] = details
    return apply_graceful_degradation(event, parser="agent_health_v1", confidence=1.0)
