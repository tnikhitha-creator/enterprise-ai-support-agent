import streamlit as st

import os
import bcrypt
from dotenv import load_dotenv

load_dotenv()


ADMIN_USERNAME = os.getenv(
    "ADMIN_USERNAME"
)

ADMIN_PASSWORD_HASH = os.getenv(
    "ADMIN_PASSWORD_HASH"
)


def _verify_password(password, password_hash):

    if not password_hash:
        return False

    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except ValueError:
        return False


def admin_login():

    st.title("🔐 Admin Login")

    username = st.text_input(
        "Username"
    )

    password = st.text_input(
        "Password",
        type="password"
    )

    if st.button("Login"):

        if (
            username == ADMIN_USERNAME
            and _verify_password(password, ADMIN_PASSWORD_HASH)
        ):

            st.session_state["admin_authenticated"] = True

            st.success(
                "Login successful"
            )

            st.rerun()

        else:

            st.error(
                "Invalid username or password"
            )


def is_admin_authenticated():

    return st.session_state.get(
        "admin_authenticated",
        False
    )


def logout():

    if st.button("Logout"):

        st.session_state["admin_authenticated"] = False

        st.rerun()