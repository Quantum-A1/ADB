# streamlit_app.py
import streamlit as st
import os
from dotenv import load_dotenv
from common import login_with_discord, exchange_code_for_token, fetch_user_info, init_db_pool

# Load secrets if needed.
if not st.secrets:
    load_dotenv()

# Initialize session state for authentication.
if "user" not in st.session_state:
    st.session_state["user"] = None
if "code_exchanged" not in st.session_state:
    st.session_state["code_exchanged"] = False

# Authentication via Discord OAuth.
if st.session_state["user"] is None and not st.session_state["code_exchanged"]:
    query_params = st.query_params  # Updated: use st.query_params instead of st.experimental_get_query_params
    if "code" in query_params:
        code_param = query_params["code"]
        code = code_param[0] if isinstance(code_param, list) else code_param
        try:
            token_data = exchange_code_for_token(code)
            user_info = fetch_user_info(token_data["access_token"])
            st.session_state["user"] = user_info
            st.session_state["code_exchanged"] = True
        except Exception as e:
            st.error(f"Authentication failed: {e}")
            st.stop()
    else:
        st.write("Please log in to access the dashboard.")
        login_with_discord()
        st.stop()

user = st.session_state.get("user")
if not user:
    st.error("User information is missing. Please log in.")
    st.stop()

st.write(f"Welcome, **{user['username']}**!")

# Authorization check.
allowed_ids = st.secrets.get("ALLOWED_DISCORD_IDS", "").split(",")
allowed_ids = [uid.strip() for uid in allowed_ids if uid.strip()]
if user["id"] not in allowed_ids:
    st.error("Access Denied: You are not authorized to view this dashboard.")
    st.stop()

# Global initialization (e.g., connection pool).
init_db_pool()

# Optionally add a logout button in the sidebar.
if st.sidebar.button("Logout", key="logout_button"):
    st.session_state.pop("user", None)
    st.write("Please refresh the page after logging out.")
