import os

import requests
import streamlit as st
from dotenv import load_dotenv

from components.charts import horizontal_bar_chart

load_dotenv()


API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")


def render_admin_dashboard():

    st.title("🛡️ Agent Hub Admin Dashboard")

    try:
        response = requests.get(
            f"{API_URL}/admin/dashboard",
            headers={"X-Admin-Api-Key": ADMIN_API_KEY or ""},
            timeout=10,
        )

        if response.status_code == 401:
            st.error("Admin API key is missing or invalid. Check ADMIN_API_KEY in frontend/.env and the backend's .env.")
            return

        data = response.json()

    except Exception as exc:
        st.error(f"Unable to load dashboard: {exc}")
        return


    metrics = data.get("metrics", {})
    knowledge = data.get("knowledge", {})
    incidents = data.get("incidents", {})
    security = data.get("security", {})



    # =====================
    # METRICS
    # =====================

    st.subheader("📊 System Overview")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Total Requests",
            metrics.get("total_requests", 0),
        )

    with c2:
        st.metric(
            "Safe Requests",
            metrics.get("safe_requests", 0),
        )

    with c3:
        st.metric(
            "Blocked Requests",
            metrics.get("blocked_requests", 0),
        )

    with c4:
        st.metric(
            "Incidents",
            metrics.get("incidents_created", 0),
        )


    intent_chart = horizontal_bar_chart(
        metrics.get("intent_counts", {}),
        "Requests by Intent",
    )

    priority_chart = horizontal_bar_chart(
        metrics.get("priority_counts", {}),
        "Requests by Priority",
        order=["critical", "high", "medium", "low"],
    )

    if intent_chart or priority_chart:

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            if intent_chart:
                st.plotly_chart(intent_chart, use_container_width=True)

        with chart_col2:
            if priority_chart:
                st.plotly_chart(priority_chart, use_container_width=True)


    st.divider()



    # =====================
    # INCIDENT CARDS
    # =====================

    st.subheader("🚨 Incident History")


    incident_list = incidents.get(
        "recent",
        [],
    )


    if not incident_list:

        st.info(
            "No incidents found."
        )

    else:

        for incident in incident_list:

            priority = incident.get(
                "priority",
                "unknown",
            )

            status = incident.get(
                "incident_status",
                "unknown",
            )


            with st.container():

                if priority == "high":
                    st.error(
                        f"🔴 HIGH PRIORITY"
                    )

                else:
                    st.warning(
                        f"🟡 {priority.upper()}"
                    )


                st.markdown(
                    f"### {incident.get('request')}"
                )


                col1, col2 = st.columns(2)


                with col1:

                    st.write(
                        "**Intent**"
                    )

                    st.write(
                        incident.get(
                            "intent",
                            "Unknown",
                        )
                    )


                    st.write(
                        "**Resolver Status**"
                    )

                    st.write(
                        incident.get(
                            "resolver_status",
                            "Unknown",
                        )
                    )


                with col2:

                    st.write(
                        "**Incident Status**"
                    )

                    st.write(
                        status
                    )


                    st.write(
                        "**Time**"
                    )

                    st.write(
                        incident.get(
                            "timestamp",
                            "",
                        )
                    )


                details = incident.get(
                    "resolver_details"
                )

                if details:

                    with st.expander(
                        "View Failure Details"
                    ):
                        st.write(details)


                st.divider()



    # =====================
    # SECURITY CARDS
    # =====================

    st.subheader(
        "🔒 Security Monitoring"
    )


    security_events = security.get(
        "recent_events",
        [],
    )


    for event in security_events:

        details = event.get(
            "details",
            {},
        )


        with st.container():

            st.error(
                "🚫 BLOCKED SECURITY REQUEST"
            )


            st.markdown(
                f"**Request:** "
                f"{details.get('message')}"
            )


            col1, col2 = st.columns(2)


            with col1:

                st.metric(
                    "Risk Score",
                    f"{details.get('security_risk_score',0)}/100",
                )


            with col2:

                st.write(
                    "**Decision**"
                )

                st.write(
                    "BLOCKED"
                )


            st.divider()



    # =====================
    # KNOWLEDGE
    # =====================

    st.subheader(
        "📚 Knowledge Usage"
    )


    usage = knowledge.get(
        "usage",
        {},
    )

    usage_chart = horizontal_bar_chart(
        usage,
        "Knowledge Base Document Usage",
        prettify_labels=False,
    )

    if usage_chart:
        st.plotly_chart(usage_chart, use_container_width=True)
    else:
        st.info("No knowledge base usage recorded yet.")