# streamlit_app.py
import streamlit as st
st.set_page_config(page_title="Welcome", page_icon="👋", layout="wide")

import os
from dotenv import load_dotenv
from common import (
    login_with_discord,
    exchange_code_for_token,
    fetch_user_info,
    init_db_pool,
    get_user_record  # new helper to get the user record and access level
)

# Load secrets if needed.
if not st.secrets:
    load_dotenv()

# --- Theme Toggle ---
# Theme Toggle snippet to place at the top of your main file:
theme_choice = st.sidebar.radio("Select Theme", options=["Light", "Dark"], index=0)
if theme_choice == "Dark":
    st.markdown(
        """
        <style>
        :root {
            --background-color: #262730;
            --text-color: #FFF;
        }
        [data-testid="stAppViewContainer"] {
            background-color: var(--background-color);
            color: var(--text-color);
        }
        [data-testid="stSidebar"] {
            background-color: #333;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        """
        <style>
        :root {
            --background-color: #FFF;
            --text-color: #000;
        }
        [data-testid="stAppViewContainer"] {
            background-color: var(--background-color);
            color: var(--text-color);
        }
        [data-testid="stSidebar"] {
            background-color: #f0f2f6;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


# Initialize session state for authentication.
if "user" not in st.session_state:
    st.session_state["user"] = None
if "code_exchanged" not in st.session_state:
    st.session_state["code_exchanged"] = False

# Authentication via Discord OAuth.
if st.session_state["user"] is None and not st.session_state["code_exchanged"]:
    query_params = st.query_params  # Using st.query_params as required
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

# Retrieve the user's access level from the database.
user_record = get_user_record(user["id"])
if user_record:
    user["access_level"] = user_record.get("access_level", "user")
else:
    user["access_level"] = "user"  # default access level

st.session_state["user"] = user

st.write(f"Welcome, **{user['username']}**! Your access level is **{user['access_level']}**.")

# (Optional) Additional authorization: restrict access if the user is not in the allowed IDs.
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
