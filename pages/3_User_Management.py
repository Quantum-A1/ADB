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
    update_user_access,
    fetch_servers,                  # all available servers
    assign_servers_to_user,         # helper function to assign servers
    get_assigned_servers_for_user   # helper function to get assigned servers
)

user = st.session_state.get("user")
access_level = user.get("access_level", "user")

# Restrict access: only admin, super-admin, or bot owner.
if access_level not in ["admin", "super-admin"] and user["id"] != BOT_OWNER_ID:
    st.error("Access Denied: Only admin, super-admin, or bot owner can access this page.")
    st.stop()

st.header("👤 User Management")
search_term = st.text_input("Search Users", "")

# Fetch user access records once
df_users_full = fetch_user_access()
if not df_users_full.empty and search_term:
    df_users = df_users_full[
        df_users_full["username"].str.contains(search_term, case=False) |
        df_users_full["discord_id"].str.contains(search_term, case=False)
    ]
else:
    df_users = df_users_full

# --- User Stats Section (Metrics & Pie Chart) ---
if not df_users.empty:
    access_counts = df_users["access_level"].value_counts().to_dict()
    total_users = len(df_users)
    user_count = access_counts.get("user", 0)
    moderator_count = access_counts.get("moderator", 0)
    admin_count = access_counts.get("admin", 0)
    super_admin_count = access_counts.get("super-admin", 0)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("👤 Total Users", total_users)
    col2.metric("🧍 User", user_count)
    col3.metric("👨‍💼 Moderator", moderator_count)
    col4.metric("✅ Admin", admin_count)
    col5.metric("☑️ Super-admin", super_admin_count)
    
    st.subheader("🔑 User Access Distribution")
    stats_df = pd.DataFrame({
        "Access Level": list(access_counts.keys()),
        "Count": list(access_counts.values())
    })
    fig = px.pie(stats_df, values="Count", names="Access Level", title="User Access Distribution")
    st.plotly_chart(fig)
else:
    st.write("No user access records found.")

# --- Current Users Table with Assigned Servers ---
st.subheader("Current Users")
if not df_users.empty:
    def get_assigned(d_id):
        servers = get_assigned_servers_for_user(d_id)
        return ", ".join(servers) if servers else "None"
    df_users["Assigned Servers"] = df_users["discord_id"].apply(get_assigned)
    st.dataframe(df_users)
else:
    st.write("No user access records found.")

# --- Add New User Section ---
st.subheader("➕ Add New User")
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

# --- Unified Edit User Section ---
st.subheader("📋 Edit User")
if not df_users.empty:
    # Build dropdown: each option is (discord_id, "username (discord_id)")
    user_options = df_users.apply(
        lambda row: (row["discord_id"], f"{row['username']} ({row['discord_id']})"), axis=1
    ).tolist()
    selected_discord_id = st.selectbox(
        "Select a user to edit",
        options=[opt[0] for opt in user_options],
        format_func=lambda x: next((opt[1] for opt in user_options if opt[0] == x), x)
    )
    # Retrieve the selected user's record.
    selected_user_record = df_users[df_users["discord_id"] == selected_discord_id].iloc[0]
    # Pre-load assigned servers for this user.
    current_assigned_servers = get_assigned_servers_for_user(selected_discord_id)
    
    # Define role hierarchy.
    hierarchy = {"user": 1, "moderator": 2, "admin": 3, "super-admin": 4}
    current_logged_in_level = hierarchy.get(user["access_level"], 1)
    selected_user_level = hierarchy.get(selected_user_record.get("access_level", "user"), 1)
    
    with st.form("edit_user_form", clear_on_submit=True):
        st.text_input("Discord ID", value=selected_user_record["discord_id"], disabled=True)
        new_username = st.text_input("Username", value=selected_user_record["username"])
        current_access = selected_user_record.get("access_level", "user")
        new_access = st.selectbox(
            "Access Level",
            options=["user", "moderator", "admin", "super-admin"],
            index=["user", "moderator", "admin", "super-admin"].index(current_access)
        )
        new_assigned_servers = st.multiselect(
            "Assigned Servers",
            options=fetch_servers(),  # all available servers
            default=current_assigned_servers
        )
        col1, col2, col3 = st.columns(3)
        update_button = col1.form_submit_button("Update User Info")
        remove_button = col2.form_submit_button("Remove User")
        update_servers_button = col3.form_submit_button("Update Server Assignments")
        
        # If not the bot owner, enforce that you cannot modify a user with equal or higher permission.
        if user["id"] != st.secrets["BOT_OWNER_ID"]:
            if update_button:
                new_level = hierarchy.get(new_access, 1)
                if current_logged_in_level <= selected_user_level:
                    st.error("You cannot update a user with equal or higher permissions than yours.")
                elif new_level > current_logged_in_level:
                    st.error("You cannot set a user's permission level to be higher than yours.")
                else:
                    update_user_access(selected_discord_id, new_username, new_access)
                    st.success("User information updated successfully.")
            if remove_button:
                if current_logged_in_level <= selected_user_level:
                    st.error("You cannot remove a user with equal or higher permissions than yours.")
                else:
                    remove_user_by_discord_id(selected_discord_id)
                    st.success("User removed successfully.")
            if update_servers_button:
                if current_logged_in_level <= selected_user_level:
                    st.error("You cannot update server assignments for a user with equal or higher permissions than yours.")
                else:
                    assign_servers_to_user(selected_discord_id, new_assigned_servers)
                    st.success("Server assignments updated successfully.")
        else:
            # Bot owner bypasses permission checks.
            if update_button:
                update_user_access(selected_discord_id, new_username, new_access)
                st.success("User information updated successfully.")
            if remove_button:
                remove_user_by_discord_id(selected_discord_id)
                st.success("User removed successfully.")
            if update_servers_button:
                assign_servers_to_user(selected_discord_id, new_assigned_servers)
                st.success("Server assignments updated successfully.")
else:
    st.write("No user records to edit.")
