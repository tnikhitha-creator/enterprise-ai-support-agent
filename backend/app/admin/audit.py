from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from backend.app.admin.models import AuditEvent
from backend.app.core.db import Base, SessionLocal, engine

Base.metadata.create_all(bind=engine)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
LEGACY_AUDIT_FILE = PROJECT_ROOT / "data" / "audit" / "events.jsonl"


def _migrate_legacy_jsonl() -> None:
    """One-time import of the old JSONL audit log into SQLite, if present."""
    if not LEGACY_AUDIT_FILE.exists():
        return

    with SessionLocal() as session:
        if session.query(AuditEvent).first() is not None:
            return

        with LEGACY_AUDIT_FILE.open("r", encoding="utf-8") as file:
            for line in file:
                if not line.strip():
                    continue

                event = json.loads(line)

                session.merge(
                    AuditEvent(
                        event_id=event.get("event_id", str(uuid.uuid4())),
                        timestamp=event.get(
                            "timestamp",
                            datetime.now(timezone.utc).isoformat(),
                        ),
                        event_type=event.get("event_type", "agent_hub_request"),
                        status=event.get("status", "unknown"),
                        details=event.get("details", {}),
                    )
                )

        session.commit()


_migrate_legacy_jsonl()


def write_audit_event(
    event_type: str,
    status: str,
    details: dict,
) -> None:
    with SessionLocal() as session:
        session.add(
            AuditEvent(
                event_id=str(uuid.uuid4()),
                timestamp=datetime.now(timezone.utc).isoformat(),
                event_type=event_type,
                status=status,
                details=details,
            )
        )
        session.commit()


def read_audit_events(
    limit: int = 100,
):
    with SessionLocal() as session:
        rows = (
            session.query(AuditEvent)
            .order_by(AuditEvent.timestamp.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "event_id": row.event_id,
                "timestamp": row.timestamp,
                "event_type": row.event_type,
                "status": row.status,
                "details": row.details,
            }
            for row in rows
        ]
