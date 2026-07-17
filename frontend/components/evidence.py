import streamlit as st


def render_evidence(agent_result):
    knowledge = agent_result.get("knowledge_base", {})

    st.subheader("📚 Evidence")

    st.caption(
        f"Source: {knowledge.get('source', 'Unknown')}"
    )

    st.info(
        knowledge.get(
            "answer_context",
            "No evidence found."
        )
    )

    st.divider()