from __future__ import annotations

from typing import Any

from backend.app.admin.audit import read_audit_events


def get_incident_history(
    limit: int = 100,
) -> list[dict[str, Any]]:
    events = read_audit_events(limit=1000)
    incidents: list[dict[str, Any]] = []

    for event in events:
        details = event.get("details", {})
        trajectory = details.get("trajectory", [])

        resolver_step = next(
            (
                step
                for step in trajectory
                if step.get("agent") == "Resolver"
            ),
            None,
        )

        if not resolver_step:
            continue
        incidents.append(
            {
                "event_id": event.get("event_id"),
                "timestamp": event.get("timestamp"),
                "request": details.get("message"),
                "intent": details.get("intent"),
                "priority": details.get("priority"),

                "incident_created": details.get(
                    "incident_created",
                    False,
                ),

                "resolver_status": resolver_step.get(
                    "status"
                ),

                "resolver_action": resolver_step.get(
                    "action"
                ),

                "resolver_details": resolver_step.get(
                    "details"
                ),

                "incident_status": (
                    "created"
                    if details.get("incident_created")
                    else (
                        "pending_external"
                        if "failed" in resolver_step.get(
                            "action",
                            ""
                        ).lower()
                        else "not_required"
                    )
                ),
            }
        )

    return incidents[:limit]
