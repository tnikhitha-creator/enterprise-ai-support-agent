from backend.app.agents.graph import build_agent_hub_graph


def test_graph_compiles_with_expected_nodes():
    graph = build_agent_hub_graph()

    node_names = set(graph.get_graph().nodes.keys())

    expected = {
        "specification",
        "planner",
        "guardian",
        "blocked_response",
        "classifier",
        "researcher",
        "resolver",
        "reviewer",
    }

    assert expected.issubset(node_names)
