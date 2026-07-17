from __future__ import annotations

from typing import Literal

from langgraph.graph import END, START, StateGraph

from backend.app.agents.nodes import (
    blocked_response_node,
    classifier_node,
    guardian_node,
    planner_node,
    researcher_node,
    resolver_node,
    reviewer_node,
    specification_node,
)
from backend.app.agents.state import AgentHubState


def route_after_guardian(
    state: AgentHubState,
) -> Literal["blocked_response", "classifier"]:
    if state.get("security_status") == "blocked":
        return "blocked_response"

    return "classifier"


def build_agent_hub_graph():
    builder = StateGraph(AgentHubState)

    builder.add_node("specification", specification_node)
    builder.add_node("planner", planner_node)
    builder.add_node("guardian", guardian_node)
    builder.add_node("blocked_response", blocked_response_node)
    builder.add_node("classifier", classifier_node)
    builder.add_node("researcher", researcher_node)
    builder.add_node("resolver", resolver_node)
    builder.add_node("reviewer", reviewer_node)

    builder.add_edge(START, "specification")
    builder.add_edge("specification", "planner")
    builder.add_edge("planner", "guardian")

    builder.add_conditional_edges(
        "guardian",
        route_after_guardian,
        {
            "blocked_response": "blocked_response",
            "classifier": "classifier",
        },
    )

    builder.add_edge("blocked_response", END)

    builder.add_edge("classifier", "researcher")
    builder.add_edge("researcher", "resolver")
    builder.add_edge("resolver", "reviewer")
    builder.add_edge("reviewer", END)

    return builder.compile()


agent_hub_graph = build_agent_hub_graph()
