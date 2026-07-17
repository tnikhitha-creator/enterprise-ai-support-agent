from __future__ import annotations

from backend.app.admin.metrics import build_admin_metrics
from backend.app.admin.knowledge_stats import build_knowledge_stats
from backend.app.admin.incidents import get_incident_history
from backend.app.admin.security_events import get_security_events


def build_admin_dashboard():
    return {
        "metrics": build_admin_metrics(),

        "knowledge": build_knowledge_stats(),

        "incidents": {
            "total": len(
                get_incident_history(limit=100)
            ),
            "recent": get_incident_history(
                limit=5
            ),
        },

        "security": {
            "recent_events": get_security_events(
                limit=5
            ),
        },
    }