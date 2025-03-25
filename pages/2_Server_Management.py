import streamlit as st
import pandas as pd
from common import (
    get_db_connection,
    release_db_connection,
    fetch_servers,
    fetch_servers_for_user,
    fetch_server_config,
    update_server_config
)

user = st.session_state.get("user")
access_level = user.get("access_level", "user")

# Determine server list based on role.
if access_level == "user":
    server_options = fetch_servers_for_user(user["id"])
else:
    server_options = fetch_servers()

st.header("Server Management")
st.write("Below is a list of your server configurations:")

# Display server configurations filtered by user permissions.
conn = get_db_connection()
try:
    with conn.cursor() as cursor:
        if access_level == "user":
            if server_options:
                placeholders = ','.join(['%s'] * len(server_options))
                query = f"SELECT * FROM guild_configs WHERE server_name IN ({placeholders})"
                cursor.execute(query, tuple(server_options))
            else:
                # If no servers are assigned, set an empty list.
                server_configs = []
        else:
            cursor.execute("SELECT * FROM guild_configs")
        # If server_configs isn't already set (in the 'user' case), fetch results.
        if 'server_configs' not in locals():
            server_configs = cursor.fetchall()
finally:
    release_db_connection(conn)

if server_configs:
    df_configs = pd.DataFrame(server_configs)
    st.dataframe(df_configs)
else:
    st.write("No server configurations found.")

st.subheader("Edit Server Configuration")
if server_options:
    selected_server = st.selectbox("Select a server to edit", options=server_options)
    config = fetch_server_config(selected_server)
    if config:
        # Only allow editing if the user is a basic user managing this server
        # or is a super-admin/bot owner.
        if access_level == "user" or access_level in ["super-admin"] or user["id"] == st.secrets["BOT_OWNER_ID"]:
            with st.form("edit_server_config_form", clear_on_submit=True):
                st.text_input("Guild ID", value=str(config["guild_id"]), disabled=True)
                st.text_input("Record ID", value=str(config["id"]), disabled=True)
                guild_name = st.text_input("Guild Name", value=config["guild_name"])
                old_server = config["server_name"]
                server_name = st.text_input("Server Name", value=config["server_name"])
                nitrado_service_id = st.text_input("Nitrado Service ID", value=config["nitrado_service_id"])
                nitrado_token = st.text_input("Nitrado Token", value=config["nitrado_token"])
                alert_channel_id = st.text_input("Alert Channel ID", value=str(config["alert_channel_id"]))
                admin_role_id = st.text_input("Admin Role ID", value=str(config["admin_role_id"]))
                submitted = st.form_submit_button("Save Changes")
                if submitted:
                    new_config = {
                        "id": config["id"],
                        "guild_id": config["guild_id"],
                        "guild_name": guild_name,
                        "server_name": server_name,
                        "nitrado_service_id": nitrado_service_id,
                        "nitrado_token": nitrado_token,
                        "alert_channel_id": alert_channel_id,
                        "admin_role_id": admin_role_id
                    }
                    update_server_config(new_config, old_server)
                    st.write("Update complete. Please refresh the page to see updated information.")
        else:
            st.write("Read-only view: You do not have permission to edit server configurations.")
    else:
        st.error("Could not fetch configuration for the selected server.")
else:
    st.write("No servers found to edit.")
