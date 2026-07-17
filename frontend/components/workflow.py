import streamlit as st


def render_workflow(agent_result):

    with st.expander("⚙️ Agent Hub Workflow"):

        trajectory = agent_result.get(
            "trajectory",
            []
        )

        for step in trajectory:

            status = step.get("status", "unknown")

            if status == "completed":
                icon = "✅"

            elif status == "skipped":
                icon = "➖"

            elif status == "blocked":
                icon = "🛡️"

            elif status == "failed":
                icon = "❌"

            else:
                icon = "⚪"

            st.write(
                f"{icon} **{step['agent']}**"
            )

            st.caption(
                step["action"]
            )