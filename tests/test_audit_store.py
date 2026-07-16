import os
import tempfile

os.environ["AUDIT_DB_PATH"] = tempfile.mktemp(suffix=".db")

from backend.app.admin.audit import read_audit_events, write_audit_event  # noqa: E402


def test_write_then_read_round_trip():
    write_audit_event(
        event_type="agent_hub_request",
        status="safe",
        details={"email": "user@example.com", "intent": "network_issue"},
    )

    events = read_audit_events(limit=10)

    assert events[0]["event_type"] == "agent_hub_request"
    assert events[0]["status"] == "safe"
    assert events[0]["details"]["intent"] == "network_issue"
    assert events[0]["event_id"]
    assert events[0]["timestamp"]


def test_read_respects_limit():
    for i in range(5):
        write_audit_event(
            event_type="agent_hub_request",
            status="safe",
            details={"seq": i},
        )

    events = read_audit_events(limit=3)

    assert len(events) == 3
