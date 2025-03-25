# pages/3_User_Management.py
import streamlit as st
import pandas as pd
from common import BOT_OWNER_ID, get_db_connection, release_db_connection, fetch_user_access, add_user_access, remove_user_access

# Retrieve the logged-in user from session state.
user = st.session_state.get("user")

if user["id"] != BOT_OWNER_ID:
    st.error("Access Denied: Only the bot owner can access this page.")
else:
    st.header("User Management")
    
    st.subheader("Current Users")
    df_users = fetch_user_access()
    if not df_users.empty:
        st.dataframe(df_users)
    else:
        st.write("No user access records found.")
    
    st.subheader("Add New User")
    with st.form("add_user_form", clear_on_submit=True):
        new_discord_id = st.text_input("Discord ID")
        new_username = st.text_input("Username")
        new_access = st.text_input("Access Level", value="user")
        add_submitted = st.form_submit_button("Add User")
        if add_submitted:
            if new_discord_id and new_username:
                add_user_access(new_discord_id, new_username, new_access)
            else:
                st.error("Please provide both Discord ID and Username.")
    
    st.subheader("Remove User")
    with st.form("remove_user_form", clear_on_submit=True):
        remove_record_id = st.text_input("Record ID to Remove")
        remove_submitted = st.form_submit_button("Remove User")
        if remove_submitted:
            if remove_record_id:
                remove_user_access(remove_record_id)
            else:
                st.error("Please provide a valid Record ID.")
