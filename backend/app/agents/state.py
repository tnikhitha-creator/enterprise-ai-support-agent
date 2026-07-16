from __future__ import annotations

from typing import Any, TypedDict


class AgentHubState(TypedDict, total=False):
    email: str
    message: str

    task_specification: dict[str, Any]
    plan: list[str]

    security_status: str
    security_risk_score: int
    security_findings: list[str]

    ai_classification: dict[str, Any]
    customer: dict[str, Any]
    knowledge_base: dict[str, Any]
    jira: dict[str, Any] | None

    verification_status: str
    verification_findings: list[str]

    trajectory: list[dict[str, Any]]
    final_response: str
    response_summary: dict[str, Any]
    error: str | None
