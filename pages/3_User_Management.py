# pages/3_User_Management.py
import streamlit as st
import pandas as pd
import plotly.express as px
from common import (
    BOT_OWNER_ID,
    get_db_connection,
    release_db_connection,
    fetch_user_access,
    add_user_access,
    remove_user_by_discord_id,
    update_user_access
)

user = st.session_state.get("user")
access_level = user.get("access_level", "user")

# Restrict access: only admin, super-admin, or bot owner.
if access_level not in ["admin", "super-admin"] and user["id"] != BOT_OWNER_ID:
    st.error("Access Denied: Only admin, super-admin, or bot owner can access this page.")
    st.stop()

st.header("User Management")

# Fetch current users.
df_users = fetch_user_access()

if not df_users.empty:
    # Display user stats similar to Dashboard.
    access_counts = df_users["access_level"].value_counts().to_dict()
    total_users = len(df_users)
    user_count = access_counts.get("user", 0)
    moderator_count = access_counts.get("moderator", 0)
    admin_count = access_counts.get("admin", 0)
    super_admin_count = access_counts.get("super-admin", 0)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Users", total_users)
    col2.metric("User", user_count)
    col3.metric("Moderator", moderator_count)
    col4.metric("Admin", admin_count)
    col5.metric("Super-admin", super_admin_count)
    
    st.subheader("User Access Distribution")
    stats_df = pd.DataFrame({
        "Access Level": list(access_counts.keys()),
        "Count": list(access_counts.values())
    })
    fig = px.pie(stats_df, values="Count", names="Access Level", title="User Access Distribution")
    st.plotly_chart(fig)
else:
    st.write("No user access records found.")

st.subheader("Current Users")
if not df_users.empty:
    st.dataframe(df_users)
else:
    st.write("No user access records found.")

st.subheader("Add New User")
with st.form("add_user_form", clear_on_submit=True):
    new_discord_id = st.text_input("Discord ID")
    new_username = st.text_input("Username")
    new_access = st.selectbox("Access Level", options=["user", "moderator", "admin", "super-admin"], index=0)
    add_submitted = st.form_submit_button("Add User")
    if add_submitted:
        if new_discord_id and new_username:
            add_user_access(new_discord_id, new_username, new_access)
        else:
            st.error("Please provide both Discord ID and Username.")

st.subheader("Edit User")
with st.form("edit_user_form", clear_on_submit=True):
    edit_discord_id = st.text_input("Discord ID of User to Edit")
    new_username = st.text_input("New Username")
    new_access = st.selectbox("New Access Level", options=["user", "moderator", "admin", "super-admin"], index=0)
    edit_submitted = st.form_submit_button("Update User")
    if edit_submitted:
        if edit_discord_id and new_username:
            update_user_access(edit_discord_id, new_username, new_access)
        else:
            st.error("Please provide the Discord ID and new username.")

st.subheader("Remove User")
with st.form("remove_user_form", clear_on_submit=True):
    remove_discord_id = st.text_input("Discord ID to Remove")
    remove_submitted = st.form_submit_button("Remove User")
    if remove_submitted:
        if remove_discord_id:
            remove_user_by_discord_id(remove_discord_id)
        else:
            st.error("Please provide a valid Discord ID.")
