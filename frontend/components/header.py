import streamlit as st


def render_header():

    st.title("Agent Hub")

    st.caption(
        "Enterprise Agentic AI Operations Platform"
    )

    st.markdown(
        """
Investigate enterprise incidents, retrieve knowledge,
analyze security risks, and recommend the best resolution.
"""
    )

    st.divider()