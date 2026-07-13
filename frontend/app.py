import requests
import streamlit as st

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Agent Hub",
    layout="wide",
)

st.title("Agent Hub")
st.caption("Enterprise Agentic AI Operations Platform")

email = st.text_input(
    "Customer email",
    value="sarah@example.com",
)

message = st.text_area(
    "Describe the issue",
    value="My password reset email never arrives and I cannot access my account.",
    height=130,
)

if st.button("Analyze request", type="primary"):
    if not email.strip() or not message.strip():
        st.warning("Enter both an email address and a support request.")
        st.stop()

    with st.spinner("Agent Hub is analyzing the request..."):
        try:
            response = requests.post(
                f"{API_URL}/support",
                json={
                    "email": email.strip(),
                    "message": message.strip(),
                },
                timeout=120,
            )
            response.raise_for_status()
            result = response.json()

        except requests.exceptions.ConnectionError:
            st.error(
                "The FastAPI backend is not running. "
                "Start it with: uvicorn backend.app.main:app --reload"
            )
            st.stop()

        except requests.exceptions.RequestException as exc:
            st.error(f"Request failed: {exc}")
            st.stop()

    agent_result = result["agent_result"]

    task_specification = agent_result.get("task_specification", {})
    trajectory = agent_result.get("trajectory", [])
    ai = agent_result.get("ai_classification", {})
    customer = agent_result.get("customer", {})
    knowledge = agent_result.get("knowledge_base", {})
    jira = agent_result.get("jira")

    st.success("Request analyzed successfully.")

    st.subheader("Agent Hub")

    completed_steps = sum(
        step.get("status") == "completed"
        for step in trajectory
    )

    st.caption(
        f"{completed_steps} of {len(trajectory)} workflow stages completed"
    )

    for step in trajectory:
        status = step.get("status", "unknown")

        if status == "completed":
            symbol = "✓"
        elif status == "skipped":
            symbol = "—"
        elif status == "failed":
            symbol = "×"
        else:
            symbol = "•"

        duration = step.get("duration_ms", 0)

        with st.container(border=True):
            st.markdown(
                f"**{symbol} {step.get('agent', 'Agent')}**"
            )
            st.caption(step.get("action", ""))
            st.write(
                f"Status: **{status.title()}** · "
                f"Duration: **{duration} ms**"
            )

            if step.get("reason"):
                st.caption(step["reason"])

            if step.get("error"):
                st.error(step["error"])

    with st.expander("View task specification"):
        st.json(task_specification)

    st.subheader("Request analysis")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Intent",
            ai.get("intent", "Unknown"),
        )

    with col2:
        st.metric(
            "Priority",
            ai.get("priority", "Unknown"),
        )

    with col3:
        ticket_status = (
            "Created"
            if jira and jira.get("created")
            else "Not created"
        )

        st.metric(
            "Incident",
            ticket_status,
        )

    st.subheader("AI summary")
    st.write(
        ai.get(
            "summary",
            "No summary generated.",
        )
    )

    st.subheader("Customer context")

    customer_col1, customer_col2 = st.columns(2)

    with customer_col1:
        st.write(
            f"**Name:** {customer.get('name', 'Unknown')}"
        )
        st.write(
            f"**Company:** {customer.get('company', 'Unknown')}"
        )

    with customer_col2:
        st.write(
            f"**Plan:** {customer.get('plan', 'Unknown')}"
        )
        st.write(
            f"**Status:** {customer.get('status', 'Unknown')}"
        )

    st.subheader("Knowledge evidence")

    source = knowledge.get("source") or "No source found"
    answer_context = knowledge.get(
        "answer_context",
        "No knowledge result found.",
    )

    st.caption(f"Source: {source}")
    st.info(answer_context)

    if jira and jira.get("created"):
        st.subheader("Incident")

        incident_col1, incident_col2 = st.columns(2)

        with incident_col1:
            st.write(
                f"**Ticket:** {jira.get('ticket_id', 'Unknown')}"
            )

        with incident_col2:
            st.write("**Status:** Created")

        if jira.get("ticket_url"):
            st.link_button(
                "Open incident",
                jira["ticket_url"],
            )

    elif jira:
        st.warning("The incident could not be created.")
        st.code(
            jira.get(
                "error",
                "Unknown Jira error",
            )
        )

    st.subheader("Final response")
    st.write(
        result.get(
            "output",
            "No final response generated.",
        )
    )

st.divider()
st.caption("Built by Nikhitha")
