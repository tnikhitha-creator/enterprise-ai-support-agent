from __future__ import annotations

from typing import Any

from langfuse import get_client, observe

from backend.app.agents.graph import agent_hub_graph

from backend.app.admin.audit import write_audit_event


@observe(name="agent_hub_request")
def run_support_agent(
    email: str,
    message: str,
) -> dict[str, Any]:
    initial_state = {
        "email": email,
        "message": message,
        "trajectory": [],
        "jira": None,
        "error": None,
    }

    result = agent_hub_graph.invoke(initial_state)

    get_client().update_current_span(
        output=result.get("final_response"),
        metadata={
            "security_status": result.get("security_status"),
            "verification_status": result.get("verification_status"),
            "trajectory": result.get("trajectory", []),
        },
    )
    write_audit_event(
        event_type="agent_hub_request",
        status=result.get("security_status", "completed"),
        details={
            "email": email,
            "message": message,
            "security_status": result.get("security_status"),
            "security_risk_score": result.get(
                "security_risk_score",
                0,
            ),
            "intent": result.get(
                "ai_classification",
                {},
            ).get("intent"),
            "priority": result.get(
                "ai_classification",
                {},
            ).get("priority"),
            "verification_status": result.get(
                "verification_status",
            ),
            "incident_created": bool(
                result.get("jira")
                and result["jira"].get("created")
            ),
            "knowledge_source": result.get(
                "knowledge_base",
                {},
            ).get("source"),
            "trajectory": result.get("trajectory", []),
        },
    )

    return {
        "hub_name": "Agent Hub",
        "task_specification": result.get("task_specification", {}),
        "plan": result.get("plan", []),
        "trajectory": result.get("trajectory", []),
        "security_status": result.get("security_status", "unknown"),
        "security_risk_score": result.get("security_risk_score", 0),
        "security_findings": result.get("security_findings", []),
        "ai_classification": result.get("ai_classification", {}),
        "customer": result.get("customer", {}),
        "knowledge_base": result.get("knowledge_base", {}),
        "jira": result.get("jira"),
        "verification_status": result.get(
            "verification_status",
            "unknown",
        ),
        "verification_findings": result.get(
            "verification_findings",
            [],
        ),
        "final_response": result.get(
            "final_response",
            "No response was generated.",
        ),
        "response_summary": result.get("response_summary", {}),
    }
