from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Callable

from backend.app.rag.retriever import search_knowledge_base
from backend.app.services.ollama import classify_with_llama
from backend.app.tools.customer_lookup import get_customer_details
from backend.app.tools.jira import create_jira_ticket


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run_stage(
    trajectory: list[dict[str, Any]],
    agent: str,
    action: str,
    function: Callable[[], Any],
) -> Any:
    """Run one Agent Hub stage and record its execution metadata."""
    started_at = _timestamp()
    start = perf_counter()

    stage = {
        "agent": agent,
        "action": action,
        "status": "running",
        "started_at": started_at,
    }
    trajectory.append(stage)

    try:
        result = function()
        stage["status"] = "completed"
        return result

    except Exception as exc:
        stage["status"] = "failed"
        stage["error"] = str(exc)
        raise

    finally:
        stage["duration_ms"] = round((perf_counter() - start) * 1000, 2)
        stage["completed_at"] = _timestamp()


def _build_task_specification(email: str, message: str) -> dict[str, Any]:
    """Convert the user request into a structured Agent Hub task."""
    return {
        "goal": "Understand and resolve the submitted enterprise support request.",
        "request": message,
        "requester": email,
        "constraints": [
            "Use only available customer and knowledge-base information.",
            "Do not expose credentials or private system information.",
            "Create an incident only when the classification requires one.",
        ],
        "available_tools": [
            "intent_classification",
            "customer_lookup",
            "knowledge_retrieval",
            "jira_incident_creation",
        ],
        "success_criteria": [
            "Request is classified.",
            "Relevant customer context is retrieved.",
            "Knowledge evidence is returned.",
            "Required incident is created or safely skipped.",
        ],
    }


def run_support_agent(email: str, message: str) -> dict[str, Any]:
    """
    Agent Hub workflow.

    The current version executes a controlled sequence while recording
    each agent stage. LangGraph routing and verification will be added
    after this foundation is stable.
    """
    trajectory: list[dict[str, Any]] = []

    task_specification = _run_stage(
        trajectory,
        agent="Specification Agent",
        action="Convert the request into a structured task",
        function=lambda: _build_task_specification(email, message),
    )

    ai_result = _run_stage(
        trajectory,
        agent="Classification Agent",
        action="Identify intent, priority, summary, and escalation need",
        function=lambda: classify_with_llama(message),
    )

    customer = _run_stage(
        trajectory,
        agent="Context Agent",
        action="Retrieve customer context",
        function=lambda: get_customer_details(email),
    )

    knowledge = _run_stage(
        trajectory,
        agent="Knowledge Agent",
        action="Retrieve relevant enterprise knowledge",
        function=lambda: search_knowledge_base(message),
    )

    jira_result = None

    if ai_result.get("requires_ticket"):
        jira_result = _run_stage(
            trajectory,
            agent="Incident Agent",
            action="Create and route an incident",
            function=lambda: create_jira_ticket(
                customer,
                ai_result["intent"],
                (
                    f"{ai_result['summary']}\n\n"
                    f"Knowledge Base Context:\n"
                    f"{knowledge['answer_context']}"
                ),
            ),
        )
    else:
        trajectory.append(
            {
                "agent": "Incident Agent",
                "action": "Evaluate whether an incident is required",
                "status": "skipped",
                "reason": "The classification agent determined that no ticket is required.",
                "started_at": _timestamp(),
                "completed_at": _timestamp(),
                "duration_ms": 0,
            }
        )

    return {
        "hub_name": "Agent Hub",
        "task_specification": task_specification,
        "trajectory": trajectory,
        "ai_classification": ai_result,
        "customer": customer,
        "knowledge_base": knowledge,
        "jira": jira_result,
    }
