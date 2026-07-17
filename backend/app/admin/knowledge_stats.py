from __future__ import annotations

from collections import Counter

from backend.app.admin.audit import read_audit_events


def build_knowledge_stats():
    events = read_audit_events(limit=1000)

    sources = Counter()

    for event in events:
        source = (
            event.get("details", {})
            .get("knowledge_source")
        )

        if source:
            sources[source] += 1

    return {
        "total_documents_used": len(sources),
        "usage": dict(sources),
    }