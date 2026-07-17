import streamlit as st


def render_customer(agent_result):
    customer = agent_result.get("customer", {})

    st.subheader("👤 Customer")

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**Name**")
        st.write(customer.get("name", "Unknown"))

        st.write(f"**Company**")
        st.write(customer.get("company", "Unknown"))

    with col2:
        st.write(f"**Plan**")
        st.write(customer.get("plan", "Unknown"))

        st.write(f"**Status**")
        st.write(customer.get("status", "Unknown"))

    st.divider()
