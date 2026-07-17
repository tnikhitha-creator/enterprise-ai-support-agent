from __future__ import annotations

from collections import Counter
from typing import Any

from backend.app.admin.audit import read_audit_events


def build_admin_metrics() -> dict[str, Any]:
    events = read_audit_events(limit=1000)

    status_counts = Counter(
        event.get("status", "unknown")
        for event in events
    )

    intent_counts = Counter(
        event.get("details", {}).get("intent")
        for event in events
        if event.get("details", {}).get("intent")
    )

    priority_counts = Counter(
        event.get("details", {}).get("priority")
        for event in events
        if event.get("details", {}).get("priority")
    )

    incidents_created = sum(
        bool(event.get("details", {}).get("incident_created"))
        for event in events
    )

    return {
        "total_requests": len(events),
        "safe_requests": status_counts.get("safe", 0),
        "blocked_requests": status_counts.get("blocked", 0),
        "review_requests": status_counts.get("review", 0),
        "incidents_created": incidents_created,
        "intent_counts": dict(intent_counts),
        "priority_counts": dict(priority_counts),
    }
