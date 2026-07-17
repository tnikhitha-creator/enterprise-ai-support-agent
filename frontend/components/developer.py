import streamlit as st


def render_developer(agent_result):

    with st.expander("🧑‍💻 Developer Details"):

        st.markdown("### Task Specification")

        st.json(
            agent_result.get(
                "task_specification",
                {}
            )
        )

        st.markdown("### Verification")

        st.write(
            agent_result.get(
                "verification_status",
                "Unknown"
            )
        )

        findings = agent_result.get(
            "verification_findings",
            []
        )

        if findings:

            for item in findings:

                st.warning(item)

        else:

            st.success(
                "No verification issues."
            )