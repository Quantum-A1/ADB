# pages/2_Server_Management.py
import streamlit as st
import pandas as pd
from common import get_db_connection, release_db_connection, fetch_servers, fetch_server_config, update_server_config

st.header("Server Management")
st.write("Below is a list of all server configurations:")

conn = get_db_connection()
try:
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM guild_configs")
        server_configs = cursor.fetchall()
finally:
    release_db_connection(conn)

if server_configs:
    df_configs = pd.DataFrame(server_configs)
    st.dataframe(df_configs)
else:
    st.write("No server configurations found.")

st.subheader("Edit Server Configuration")
server_options = fetch_servers()
if server_options:
    selected_server = st.selectbox("Select a server to edit", options=server_options)
    config = fetch_server_config(selected_server)
    if config:
        with st.form("edit_server_config_form", clear_on_submit=True):
            st.text_input("Guild ID", value=str(config["guild_id"]), disabled=True)
            st.text_input("Record ID", value=str(config["id"]), disabled=True)
            guild_name = st.text_input("Guild Name", value=config["guild_name"])
            old_server = config["server_name"]  # Save the old server name.
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
        st.error("Could not fetch configuration for the selected server.")
else:
    st.write("No servers found to edit.")
