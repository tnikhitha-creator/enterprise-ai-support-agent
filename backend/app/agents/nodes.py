from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.app.agents.state import AgentHubState
from backend.app.rag.retriever import search_knowledge_base
from backend.app.services.ollama import classify_with_llama
from backend.app.tools.customer_lookup import get_customer_details
from backend.app.tools.jira import create_jira_ticket


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _trajectory_entry(
    agent: str,
    action: str,
    status: str = "completed",
    details: str | None = None,
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "agent": agent,
        "action": action,
        "status": status,
        "timestamp": _timestamp(),
    }

    if details:
        entry["details"] = details

    return entry


def specification_node(state: AgentHubState) -> dict[str, Any]:
    """Convert the incoming request into a structured task specification."""
    specification = {
        "goal": "Resolve or safely escalate the enterprise support request.",
        "requester": state["email"],
        "request": state["message"],
        "constraints": [
            "Use only available customer and enterprise knowledge.",
            "Do not expose credentials or restricted information.",
            "Create an incident only when required.",
        ],
        "success_criteria": [
            "Classify the request.",
            "Retrieve relevant context.",
            "Provide grounded guidance.",
            "Create or skip an incident appropriately.",
            "Verify the final response.",
        ],
    }

    return {
        "task_specification": specification,
        "trajectory": state.get("trajectory", [])
        + [
            _trajectory_entry(
                "Specification",
                "Converted the request into a structured task",
            )
        ],
    }


def planner_node(state: AgentHubState) -> dict[str, Any]:
    """
    Generate an execution strategy for Agent Hub.
    """

    prompt = f"""
        You are the planning engine of an enterprise AI support platform.

        User Request:
        {state["message"]}

        Return ONLY valid JSON.

        Example:

        {{
            "goal":"...",
            "priority":"Low | Medium | High | Critical",
            "reasoning":"...",
            "steps":[
                "...",
                "...",
                "...",
                "..."
            ]
        }}
        """

    response = classify_with_llama(prompt)

    if isinstance(response, dict):
        plan = response

    else:

        plan = {
            "goal": state["message"],
            "priority": "Medium",
            "reasoning": "Fallback planner used.",
            "steps": [
                "Understand request",
                "Retrieve knowledge",
                "Resolve issue",
                "Verify response",
            ],
        }

    return {
        "plan": plan,
        "trajectory": state.get("trajectory", [])
        + [
            _trajectory_entry(
                "Planner",
                "Generated an execution strategy",
                details=plan.get(
                    "priority",
                    "Unknown",
                ),
            )
        ],
    }



def guardian_node(state: AgentHubState) -> dict[str, Any]:
    """Enterprise security guardrails."""

    message = state["message"].lower()

    findings = []
    risk_score = 0

    checks = {
        "Prompt Injection": [
            "ignore previous instructions",
            "ignore all instructions",
            "override system",
            "forget previous instructions",
        ],
        "Secret Request": [
            "api key",
            "password",
            "secret token",
            "private key",
        ],
        "Role Override": [
            "act as administrator",
            "act as root",
            "grant me admin",
        ],
        "Tool Misuse": [
            "delete database",
            "delete all tickets",
            "disable security",
            "run shell",
        ],
    }

    for category, patterns in checks.items():
        for pattern in patterns:
            if pattern in message:
                findings.append(f"{category}: {pattern}")
                risk_score += 25

    risk_score = min(risk_score, 100)

    if risk_score >= 50:
        security_status = "blocked"
    elif risk_score >= 25:
        security_status = "review"
    else:
        security_status = "safe"

    return {
        "security_status": security_status,
        "security_risk_score": risk_score,
        "security_findings": findings,
        "trajectory": state.get("trajectory", []) + [
            _trajectory_entry(
                "Guardian",
                "Evaluated enterprise security policies",
                status="blocked" if security_status == "blocked" else "completed",
                details=f"Risk Score: {risk_score}",
            )
        ],
    }

def blocked_response_node(state: AgentHubState) -> dict[str, Any]:
    """Generate a safe response when Guardian blocks a request."""
    return {
        "verification_status": "blocked",
        "verification_findings": [
            "The request triggered the security policy."
        ],
        "final_response": (
            "Nice try 😄 Enterprise secrets stay secret. "
            "This request was blocked because it may be attempting to "
            "override system instructions or access restricted information."
        ),
        "trajectory": state.get("trajectory", [])
        + [
            _trajectory_entry(
                "Reviewer",
                "Confirmed that the blocked request should not continue",
                status="blocked",
            )
        ],
    }


def classifier_node(state: AgentHubState) -> dict[str, Any]:
    classification = classify_with_llama(state["message"])

    return {
        "ai_classification": classification,
        "trajectory": state.get("trajectory", [])
        + [
            _trajectory_entry(
                "Classifier",
                "Identified intent, priority, and escalation need",
                details=f"Intent: {classification.get('intent', 'unknown')}",
            )
        ],
    }


def researcher_node(state: AgentHubState) -> dict[str, Any]:
    customer = get_customer_details(state["email"])
    knowledge = search_knowledge_base(state["message"])

    return {
        "customer": customer,
        "knowledge_base": knowledge,
        "trajectory": state.get("trajectory", [])
        + [
            _trajectory_entry(
                "Researcher",
                "Retrieved customer context and knowledge evidence",
                details=f"Source: {knowledge.get('source', 'none')}",
            )
        ],
    }


def resolver_node(state: AgentHubState) -> dict[str, Any]:
    classification = state["ai_classification"]
    customer = state["customer"]
    knowledge = state["knowledge_base"]

    jira_result = None

    if classification.get("requires_ticket"):
        jira_result = create_jira_ticket(
            customer,
            classification.get("intent", "support_request"),
            (
                f"{classification.get('summary', state['message'])}\n\n"
                f"Knowledge Base Context:\n"
                f"{knowledge.get('answer_context', 'No context found.')}"
            ),
        )

        if jira_result and jira_result.get("created"):
            action = "Created and routed an incident"
            status = "completed"

        elif jira_result:
            action = "Incident creation failed, recorded for follow-up"
            status = "completed"

            jira_result["fallback_incident"] = True
            jira_result["fallback_status"] = "pending_external"

        else:
            action = "Incident creation was skipped"
            status = "skipped"

    else:
        action = "Resolved the request without creating an incident"
        status = "skipped"

    return {
        "jira": jira_result,
        "trajectory": state.get("trajectory", [])
        + [
            _trajectory_entry(
                "Resolver",
                action,
                status=status,
                details=(
                    jira_result.get("error")
                    if jira_result
                    and not jira_result.get("created")
                    else None
                ),
            )
        ],
    }

def _build_incident_summary(jira: dict[str, Any] | None) -> dict[str, Any]:
    if jira and jira.get("created"):
        return {
            "status": "created",
            "ticket_id": jira.get("ticket_id"),
            "ticket_url": jira.get("ticket_url"),
        }

    if jira and jira.get("fallback_status") == "pending_external":
        return {
            "status": "pending_external",
            "ticket_id": None,
            "ticket_url": None,
        }

    if jira:
        return {
            "status": "failed",
            "ticket_id": None,
            "ticket_url": None,
        }

    return {
        "status": "not_required",
        "ticket_id": None,
        "ticket_url": None,
    }


def reviewer_node(state: AgentHubState) -> dict[str, Any]:
    classification = state.get("ai_classification", {})
    knowledge = state.get("knowledge_base", {})
    findings: list[str] = []

    answer_context = knowledge.get("answer_context")

    if not answer_context:
        findings.append("No supporting knowledge evidence was retrieved.")

    if not classification.get("summary"):
        findings.append("The classification did not include a summary.")

    verification_status = "passed" if not findings else "needs_review"

    incident = _build_incident_summary(state.get("jira"))

    actions = [
        line.strip()
        for line in (answer_context or "").split("\n")
        if line.strip()
    ] or ["No specific action steps were found in the knowledge base."]

    response_summary = {
        "summary": classification.get("summary", "The request was analyzed."),
        "priority": classification.get("priority", "medium"),
        "actions": actions,
        "incident": incident,
        "evidence": {
            "source": knowledge.get("source"),
            "confidence": knowledge.get("confidence", 0),
            "context": answer_context or "No reliable knowledge evidence was found.",
        },
    }

    incident_text = (
        f" An incident was created with ID {incident['ticket_id']}."
        if incident["status"] == "created"
        else ""
    )

    final_response = (
        f"{response_summary['summary']} "
        f"{response_summary['evidence']['context']}"
        f"{incident_text}"
    )

    return {
        "verification_status": verification_status,
        "verification_findings": findings,
        "final_response": final_response,
        "response_summary": response_summary,
        "trajectory": state.get("trajectory", [])
        + [
            _trajectory_entry(
                "Reviewer",
                "Verified grounding and response completeness",
                status=(
                    "completed"
                    if verification_status == "passed"
                    else "needs_review"
                ),
                details=f"Verification: {verification_status}",
            )
        ],
    }
