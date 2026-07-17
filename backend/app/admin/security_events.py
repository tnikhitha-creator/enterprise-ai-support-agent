from __future__ import annotations

from typing import Any

from backend.app.admin.audit import read_audit_events


def get_security_events(
    limit: int = 100,
) -> list[dict[str, Any]]:
    events = read_audit_events(limit=1000)

    security_events = [
        event
        for event in events
        if event.get("details", {}).get("security_status")
        in {"blocked", "review"}
    ]

    return security_events[:limit]
