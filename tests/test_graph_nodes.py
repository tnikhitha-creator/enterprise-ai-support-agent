from backend.app.agents import nodes
from backend.app.agents.graph import route_after_guardian


def test_route_after_guardian_sends_blocked_requests_to_blocked_response():
    assert route_after_guardian({"security_status": "blocked"}) == "blocked_response"


def test_route_after_guardian_sends_safe_requests_to_classifier():
    assert route_after_guardian({"security_status": "safe"}) == "classifier"
    assert route_after_guardian({"security_status": "review"}) == "classifier"


def test_blocked_response_node_produces_safe_refusal():
    result = nodes.blocked_response_node({"trajectory": []})

    assert result["verification_status"] == "blocked"
    assert "blocked" in result["final_response"].lower()


def test_reviewer_node_flags_missing_knowledge_and_summary():
    state = {
        "ai_classification": {},
        "knowledge_base": {},
        "jira": None,
        "trajectory": [],
    }

    result = nodes.reviewer_node(state)

    assert result["verification_status"] == "needs_review"
    assert len(result["verification_findings"]) == 2


def test_reviewer_node_passes_when_grounded_and_includes_incident_id():
    state = {
        "ai_classification": {"summary": "Reset the VPN client and reconnect.", "priority": "high"},
        "knowledge_base": {"answer_context": "See vpn_help.txt for reconnection steps.", "source": "vpn_help.txt", "confidence": 80},
        "jira": {"created": True, "ticket_id": "OPS-42", "ticket_url": "https://example.atlassian.net/browse/OPS-42"},
        "trajectory": [],
    }

    result = nodes.reviewer_node(state)

    assert result["verification_status"] == "passed"
    assert result["verification_findings"] == []
    assert "OPS-42" in result["final_response"]


def test_reviewer_node_builds_structured_response_summary():
    state = {
        "ai_classification": {"summary": "Reset the VPN client.", "priority": "high"},
        "knowledge_base": {
            "answer_context": "Restart the router.\nReconnect the VPN client.",
            "source": "vpn_help.txt",
            "confidence": 75,
        },
        "jira": {"created": True, "ticket_id": "OPS-42", "ticket_url": "https://example.atlassian.net/browse/OPS-42"},
        "trajectory": [],
    }

    result = nodes.reviewer_node(state)
    summary = result["response_summary"]

    assert summary["summary"] == "Reset the VPN client."
    assert summary["priority"] == "high"
    assert summary["actions"] == ["Restart the router.", "Reconnect the VPN client."]
    assert summary["incident"] == {
        "status": "created",
        "ticket_id": "OPS-42",
        "ticket_url": "https://example.atlassian.net/browse/OPS-42",
    }
    assert summary["evidence"]["source"] == "vpn_help.txt"
    assert summary["evidence"]["confidence"] == 75


def test_reviewer_node_marks_incident_not_required_without_jira():
    state = {
        "ai_classification": {"summary": "No ticket needed."},
        "knowledge_base": {},
        "jira": None,
        "trajectory": [],
    }

    result = nodes.reviewer_node(state)

    assert result["response_summary"]["incident"]["status"] == "not_required"


def test_reviewer_node_marks_incident_pending_external_on_jira_failure():
    state = {
        "ai_classification": {"summary": "Ticket needed but Jira failed."},
        "knowledge_base": {},
        "jira": {"created": False, "fallback_status": "pending_external"},
        "trajectory": [],
    }

    result = nodes.reviewer_node(state)

    assert result["response_summary"]["incident"]["status"] == "pending_external"


def test_resolver_node_skips_ticket_when_not_required():
    state = {
        "ai_classification": {"requires_ticket": False},
        "customer": {"name": "Jane Doe"},
        "knowledge_base": {},
        "trajectory": [],
    }

    result = nodes.resolver_node(state)

    assert result["jira"] is None
    assert result["trajectory"][-1]["status"] == "skipped"


def test_resolver_node_creates_ticket_when_required(monkeypatch):
    def fake_create_jira_ticket(customer, intent, message):
        return {"created": True, "ticket_id": "OPS-7", "ticket_url": "https://example.atlassian.net/browse/OPS-7"}

    monkeypatch.setattr(nodes, "create_jira_ticket", fake_create_jira_ticket)

    state = {
        "email": "user@example.com",
        "message": "My VPN is down",
        "ai_classification": {"requires_ticket": True, "intent": "network_issue", "summary": "VPN down"},
        "customer": {"name": "Jane Doe"},
        "knowledge_base": {"answer_context": "Try reconnecting the VPN client."},
        "trajectory": [],
    }

    result = nodes.resolver_node(state)

    assert result["jira"]["created"] is True
    assert result["trajectory"][-1]["status"] == "completed"


def test_resolver_node_records_failure_as_pending_external(monkeypatch):
    def fake_create_jira_ticket(customer, intent, message):
        return {"created": False, "error": "403 Forbidden", "status_code": 403}

    monkeypatch.setattr(nodes, "create_jira_ticket", fake_create_jira_ticket)

    state = {
        "email": "user@example.com",
        "message": "My VPN is down",
        "ai_classification": {"requires_ticket": True, "intent": "network_issue", "summary": "VPN down"},
        "customer": {"name": "Jane Doe"},
        "knowledge_base": {},
        "trajectory": [],
    }

    result = nodes.resolver_node(state)

    assert result["jira"]["created"] is False
    assert result["jira"]["fallback_status"] == "pending_external"
