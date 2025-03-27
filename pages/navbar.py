import streamlit as st

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
