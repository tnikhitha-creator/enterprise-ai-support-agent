import os

import requests
import streamlit as st

from components.customer import render_customer
from components.developer import render_developer
from components.evidence import render_evidence
from components.header import render_header
from components.resolution import render_resolution
from components.workflow import render_workflow
from components.admin_dashboard import render_admin_dashboard

from components.auth import (
    admin_login,
    is_admin_authenticated,
    logout,
)


API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")


st.set_page_config(
    page_title="Agent Hub",
    layout="wide",
)


render_header()


page = st.sidebar.selectbox(
    "Navigation",
    [
        "Support Agent",
        "Admin Dashboard",
    ],
)


if page == "Admin Dashboard":

    if not is_admin_authenticated():

        admin_login()

        st.stop()


    logout()

    render_admin_dashboard()

    st.stop()



email = st.text_input(
    "Your email",
    placeholder="you@company.com",
)


message = st.text_area(
    "What would you like Agent Hub to investigate?",
    placeholder="Describe an IT, security, account, or billing issue...",
    height=180,
)


if st.button(
    "🚀 Analyze Request",
    type="primary",
    use_container_width=True,
):

    if not email.strip() or not message.strip():

        st.warning(
            "Enter both an email address and a request."
        )

        st.stop()


    with st.spinner(
        "Agent Hub is investigating..."
    ):

        try:

            response = requests.post(
                f"{API_URL}/support",
                json={
                    "email": email.strip(),
                    "message": message.strip(),
                },
                timeout=300,
            )


        except requests.exceptions.ConnectionError:

            st.error(
                "The FastAPI backend is not running."
            )

            st.stop()


        except requests.exceptions.RequestException as exc:

            st.error(
                f"Request failed: {exc}"
            )

            st.stop()



        if not response.ok:

            st.error(
                f"Agent Hub API error: {response.text}"
            )

            st.stop()



        result = response.json()



    agent_result = result["agent_result"]

    security_status = agent_result.get(
        "security_status",
        "unknown",
    )


    if security_status == "blocked":

        st.error(
            "🛡️ Security Policy Triggered"
        )


        st.info(
            agent_result.get(
                "final_response",
                "Request blocked.",
            )
        )


        col1, col2 = st.columns(2)


        with col1:

            st.metric(
                "Risk Score",
                f"{agent_result.get('security_risk_score',0)}/100",
            )


        with col2:

            st.metric(
                "Status",
                "Blocked",
            )


        render_workflow(
            agent_result
        )


        render_developer(
            agent_result
        )


    else:

        render_resolution(
            agent_result
        )

        render_customer(
            agent_result
        )

        render_evidence(
            agent_result
        )

        render_workflow(
            agent_result
        )

        render_developer(
            agent_result
        )



st.divider()

st.caption(
    "Built by Nikhitha"
)