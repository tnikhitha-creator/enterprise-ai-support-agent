import streamlit as st


def render_resolution(agent_result):
    st.subheader("Resolution Summary")

    ai = agent_result.get("ai_classification", {})
    knowledge = agent_result.get("knowledge_base", {})
    jira = agent_result.get("jira")

    st.success(
    ai.get(
        "summary",
        "The request has been analyzed."
        )
    )

    st.markdown("### Recommended Actions")

    context = knowledge.get("answer_context", "")

    if context:
        for line in context.split("\n"):
            line = line.strip()

            if line:
                st.markdown(f"- {line}")
    else:
        st.info("No recommendations available.")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Priority",
            ai.get("priority", "Unknown").title(),
        )

    with col2:
        incident_status = (
            "Created"
            if jira and jira.get("created")
            else "Not Created"
        )

        st.metric("Incident", incident_status)

    st.divider()
