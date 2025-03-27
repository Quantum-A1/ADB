# streamlit_app.py
import streamlit as st
import os
from dotenv import load_dotenv
from common import (
    login_with_discord,
    exchange_code_for_token,
    fetch_user_info,
    init_db_pool,
    get_user_record  # helper to get the user record and access level
)

st.set_page_config(layout="wide")

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
    st.error("Your account is not authorized. Please contact an administrator.")
    st.stop()

st.session_state["user"] = user

st.write(f"Welcome, **{user['username']}**! Your access level is **{user['access_level']}**.")
st.write("**Please use the navigation bar on the left to see different parts of the ADB Dashboard**.")

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

# Define pages for each category.
pages = {
    "General": {
        "Dashboard": "dashboard",
        "Server Management": "server_management",
        "Real Time Monitoring": "real_time_monitoring",
        "Logged Accounts": "logged_accounts",
        "Feedback": "feedback"
    },
    "Administrator": {
        "Activity Logs": "activity_logs",
        "User Management": "user_management"
    }
}

# Get the current user's access level from session_state.
user = st.session_state.get("user", {})
access_level = user.get("access_level", "user")

st.sidebar.title("Navigation")

# Display the General category (available to everyone).
st.sidebar.header("General")
selected_general = st.sidebar.radio("General Pages", list(pages["General"].keys()), key="general_nav")

# Initialize selected_page with the general page.
selected_page = pages["General"][selected_general]

# If the user has moderator or higher access, also display Administrator category.
if access_level in ["moderator", "admin", "super-admin"]:
    st.sidebar.header("Administrator")
    selected_admin = st.sidebar.radio("Admin Pages", list(pages["Administrator"].keys()), key="admin_nav")
    # You can decide to override the selected_page if an admin page is selected.
    if selected_admin:
        selected_page = pages["Administrator"][selected_admin]

# Save the selection to session_state.
st.session_state["selected_page"] = selected_page

st.sidebar.markdown("---")
st.sidebar.write(f"**Current Page:** {selected_page}")

# Example page rendering logic:
st.write(f"### You are now viewing: {selected_page}")

if selected_page == "dashboard":
    st.write("Dashboard content goes here...")
elif selected_page == "server_management":
    st.write("Server Management content goes here...")
elif selected_page == "real_time_monitoring":
    st.write("Real Time Monitoring content goes here...")
elif selected_page == "logged_accounts":
    st.write("Logged Accounts content goes here...")
elif selected_page == "feedback":
    st.write("Feedback content goes here...")
elif selected_page == "activity_logs":
    st.write("Activity Logs content goes here...")
elif selected_page == "user_management":
    st.write("User Management content goes here...")
else:
    st.write("Page not found.")