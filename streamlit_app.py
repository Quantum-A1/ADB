import streamlit as st
import pymysql
import pandas as pd
import os
from dotenv import load_dotenv
import requests
from urllib.parse import urlencode
import plotly.express as px
import pymysql.err
import queue

# ------------------------------------------------------------------------------
# Database Connection Pooling
# ------------------------------------------------------------------------------
connection_pool = queue.Queue(maxsize=10)

def init_db_pool():
    """Pre-populate the connection pool with 10 connections."""
    for _ in range(10):
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            autocommit=True,
            cursorclass=pymysql.cursors.DictCursor
        )
        connection_pool.put(conn)

def get_db_connection():
    """Get a connection from the pool if available; otherwise, create a new one."""
    try:
        conn = connection_pool.get_nowait()
        if not conn.open:
            conn = pymysql.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASS,
                database=DB_NAME,
                autocommit=True,
                cursorclass=pymysql.cursors.DictCursor
            )
        return conn
    except queue.Empty:
        return pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            autocommit=True,
            cursorclass=pymysql.cursors.DictCursor
        )

def release_db_connection(conn):
    """Return the connection to the pool if not full; otherwise, close it."""
    try:
        connection_pool.put_nowait(conn)
    except queue.Full:
        conn.close()

# ------------------------------------------------------------------------------
# Authentication via Discord OAuth
# ------------------------------------------------------------------------------
if not st.secrets:
    load_dotenv()

if "user" not in st.session_state:
    st.session_state["user"] = None
if "code_exchanged" not in st.session_state:
    st.session_state["code_exchanged"] = False

DB_HOST = st.secrets.get("DB_HOST") or os.getenv("DB_HOST")
DB_USER = st.secrets.get("DB_USER") or os.getenv("DB_USER")
DB_PASS = st.secrets.get("DB_PASS") or os.getenv("DB_PASS")
DB_NAME = st.secrets.get("DB_NAME") or os.getenv("DB_NAME")

DISCORD_CLIENT_ID = st.secrets.get("DISCORD_CLIENT_ID") or os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = st.secrets.get("DISCORD_CLIENT_SECRET") or os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = st.secrets.get("DISCORD_REDIRECT_URI") or os.getenv("DISCORD_REDIRECT_URI")

# BOT_OWNER_ID should be set in your secrets for the bot owner’s Discord ID.
BOT_OWNER_ID = st.secrets.get("BOT_OWNER_ID") or os.getenv("BOT_OWNER_ID")

DISCORD_OAUTH_URL = "https://discord.com/api/oauth2/authorize"
DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"
DISCORD_API_URL = "https://discord.com/api/users/@me"

def login_with_discord():
    params = {
        "client_id": DISCORD_CLIENT_ID,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify email"
    }
    auth_url = DISCORD_OAUTH_URL + "?" + urlencode(params)
    st.markdown(f"[**Login with Discord**]({auth_url})", unsafe_allow_html=True)

def exchange_code_for_token(code):
    data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": DISCORD_REDIRECT_URI
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
    response = requests.post(DISCORD_TOKEN_URL, data=data, headers=headers)
    if response.status_code != 200:
        st.error("Token exchange failed: " + response.text)
        response.raise_for_status()
    return response.json()

def fetch_user_info(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(DISCORD_API_URL, headers=headers)
    response.raise_for_status()
    return response.json()

if st.session_state["user"] is None and not st.session_state["code_exchanged"]:
    query_params = st.query_params
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

allowed_ids = st.secrets.get("ALLOWED_DISCORD_IDS", "").split(",")
allowed_ids = [uid.strip() for uid in allowed_ids if uid.strip()]
if user["id"] not in allowed_ids:
    st.error("Access Denied: You are not authorized to view this dashboard.")
    st.stop()

# ------------------------------------------------------------------------------
# Sidebar Navigation, Logo, and Logout
# ------------------------------------------------------------------------------
logo_url = "https://cdn.discordapp.com/attachments/1353449300889440297/1354166635816026233/adb.png?ex=67e44d75&is=67e2fbf5&hm=bc63d8bb063402b32dbf61c141bb87a13f791b8a89ddab45d0e551a3b13c7532&"
st.sidebar.image(logo_url, width=150)
# Build navigation options; include "User Management" if user is the bot owner.
nav_options = ["Dashboard", "Server Management"]
if user["id"] == BOT_OWNER_ID:
    nav_options.append("User Management")
page = st.sidebar.radio("Navigation", nav_options)
if st.sidebar.button("Logout", key="logout_button"):
    st.session_state.pop("user", None)
    st.write("Please refresh the page after logging out.")

# ------------------------------------------------------------------------------
# Database Connection and Helper Functions (using Connection Pooling)
# ------------------------------------------------------------------------------
def get_db_connection_direct():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )

# In all DB functions, we use get_db_connection() from our pool and then release it.
def get_db_connection():
    return get_db_connection_direct()  # Using our pooling functions below

def fetch_stats(server_name=None):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            total_query = "SELECT COUNT(*) AS total_players FROM players"
            if server_name and server_name != "All":
                total_query += " WHERE LOWER(TRIM(server_name)) LIKE CONCAT('%%', LOWER(TRIM(%s)), '%%')"
                cursor.execute(total_query, (server_name,))
            else:
                cursor.execute(total_query)
            total_players = cursor.fetchone()["total_players"]

            flagged_query = "SELECT COUNT(*) AS flagged_accounts FROM players WHERE alt_flag = TRUE"
            if server_name and server_name != "All":
                flagged_query += " AND LOWER(TRIM(server_name)) LIKE CONCAT('%%', LOWER(TRIM(%s)), '%%')"
                cursor.execute(flagged_query, (server_name,))
            else:
                cursor.execute(flagged_query)
            flagged_accounts = cursor.fetchone()["flagged_accounts"]

            watchlisted_query = "SELECT COUNT(*) AS watchlisted_accounts FROM players WHERE watchlisted = TRUE"
            if server_name and server_name != "All":
                watchlisted_query += " AND LOWER(TRIM(server_name)) LIKE CONCAT('%%', LOWER(TRIM(%s)), '%%')"
                cursor.execute(watchlisted_query, (server_name,))
            else:
                cursor.execute(watchlisted_query)
            watchlisted_accounts = cursor.fetchone()["watchlisted_accounts"]

            whitelisted_query = "SELECT COUNT(*) AS whitelisted_accounts FROM players WHERE whitelist = TRUE"
            if server_name and server_name != "All":
                whitelisted_query += " AND LOWER(TRIM(server_name)) LIKE CONCAT('%%', LOWER(TRIM(%s)), '%%')"
                cursor.execute(whitelisted_query, (server_name,))
            else:
                cursor.execute(whitelisted_query)
            whitelisted_accounts = cursor.fetchone()["whitelisted_accounts"]
    finally:
        release_db_connection(conn)

    return {
        "total_players": total_players,
        "flagged_accounts": flagged_accounts,
        "watchlisted_accounts": watchlisted_accounts,
        "whitelisted_accounts": whitelisted_accounts
    }

def fetch_trend_data(server_name=None):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            base_query = """
                SELECT DATE(timestamp) AS date, COUNT(*) AS count
                FROM player_history
            """
            if server_name and server_name != "All":
                base_query += " WHERE LOWER(TRIM(server_name)) LIKE CONCAT('%%', LOWER(TRIM(%s)), '%%')"
                base_query += " GROUP BY DATE(timestamp) ORDER BY date ASC"
                cursor.execute(base_query, (server_name,))
            else:
                base_query += " GROUP BY DATE(timestamp) ORDER BY date ASC"
                cursor.execute(base_query)
            rows = cursor.fetchall()
    finally:
        release_db_connection(conn)

    return pd.DataFrame(rows)

def fetch_servers():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT DISTINCT server_name FROM guild_configs")
            rows = cursor.fetchall()
    finally:
        release_db_connection(conn)
    return [row["server_name"] for row in rows if row["server_name"]]

# New helper: update players table with the new server name.
def update_players_server_name(old_server, new_server):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            query = """
            UPDATE players
            SET server_name = %s
            WHERE LOWER(TRIM(server_name)) = LOWER(TRIM(%s))
            """
            cursor.execute(query, (new_server, old_server))
            conn.commit()
    finally:
        release_db_connection(conn)

# Update server config in guild_configs; also update players if server name changes.
def update_server_config(new_config, old_server):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            query = """
            UPDATE guild_configs SET 
                guild_name = %s, 
                server_name = %s, 
                nitrado_service_id = %s, 
                nitrado_token = %s, 
                alert_channel_id = %s, 
                admin_role_id = %s 
            WHERE id = %s
            """
            cursor.execute(query, (
                new_config["guild_name"],
                new_config["server_name"],
                new_config["nitrado_service_id"],
                new_config["nitrado_token"],
                new_config["alert_channel_id"],
                new_config["admin_role_id"],
                new_config["id"]
            ))
            conn.commit()
            st.success("Server configuration updated! Please refresh the page to see changes.")
            # If the server name has changed, update the players table.
            if new_config["server_name"].strip().lower() != old_server.strip().lower():
                update_players_server_name(old_server, new_config["server_name"])
                st.success("All player records updated with the new server name!")
    except pymysql.err.IntegrityError as e:
        if e.args[0] == 1062:
            st.error("Duplicate entry error: This server name already exists for this guild. Please choose a different server name.")
        else:
            st.error(f"Database integrity error: {e}")
    except Exception as e:
        st.error(f"Error updating config: {e}")
    finally:
        release_db_connection(conn)

def fetch_server_config(server_name):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM guild_configs WHERE server_name = %s", (server_name,))
            return cursor.fetchone()
    finally:
        release_db_connection(conn)

# ------------------------------------------------------------------------------
# User Management Functions (for Bot Owner)
# ------------------------------------------------------------------------------
def fetch_user_access():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM user_access")
            rows = cursor.fetchall()
    finally:
        release_db_connection(conn)
    return pd.DataFrame(rows)

def add_user_access(discord_id, username, access_level):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            query = """
            INSERT INTO user_access (discord_id, username, access_level)
            VALUES (%s, %s, %s)
            """
            cursor.execute(query, (discord_id, username, access_level))
            conn.commit()
            st.success("User added successfully.")
    except pymysql.err.IntegrityError as e:
        st.error(f"Error: A user with that Discord ID may already exist. {e}")
    finally:
        release_db_connection(conn)

def remove_user_access(record_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            query = "DELETE FROM user_access WHERE id = %s"
            cursor.execute(query, (record_id,))
            conn.commit()
            st.success("User removed successfully.")
    except Exception as e:
        st.error(f"Error removing user: {e}")
    finally:
        release_db_connection(conn)

# ------------------------------------------------------------------------------
# Dashboard Page (Global Stats & Trends)
# ------------------------------------------------------------------------------
def dashboard_page():
    st.header("Dashboard")
    
    # Global Server Selector affects both summary stats and trends.
    server_options = ["All"] + fetch_servers()
    selected_server = st.selectbox("Select Server (for all stats)", options=server_options)
    
    # Fetch and display stats.
    stats = fetch_stats(selected_server)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Players", stats["total_players"])
    col2.metric("Flagged Accounts", stats["flagged_accounts"])
    col3.metric("Watchlisted Accounts", stats["watchlisted_accounts"])
    col4.metric("Whitelisted Accounts", stats["whitelisted_accounts"])
    
    # Pie chart: Only flagged, watchlisted, and whitelisted accounts.
    summary_df = pd.DataFrame({
        "Metric": ["Flagged Accounts", "Watchlisted Accounts", "Whitelisted Accounts"],
        "Value": [stats["flagged_accounts"], stats["watchlisted_accounts"], stats["whitelisted_accounts"]]
    })
    st.subheader("Summary Statistics Distribution")
    fig = px.pie(summary_df, values="Value", names="Metric", title="Summary Distribution")
    st.plotly_chart(fig)
    
    st.header("Alt Detection Trends")
    df_trend = fetch_trend_data(selected_server)
    if not df_trend.empty:
        df_trend['date'] = pd.to_datetime(df_trend['date'])
        df_trend.set_index('date', inplace=True)
        st.line_chart(df_trend)
    else:
        st.write("No trend data available")

# ------------------------------------------------------------------------------
# Server Management Page (Manage/Edit Server Configurations)
# ------------------------------------------------------------------------------
def server_management_page():
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

# ------------------------------------------------------------------------------
# User Management Page (for Bot Owner)
# ------------------------------------------------------------------------------
def user_management_page():
    if user["id"] != BOT_OWNER_ID:
        st.error("Access Denied: Only the bot owner can access this page.")
        return

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

# ------------------------------------------------------------------------------
# Main Application Navigation
# ------------------------------------------------------------------------------
def main():
    st.title("Alt Detection Dashboard")
    init_db_pool()  # Initialize the connection pool
    
    nav_options = ["Dashboard", "Server Management"]
    if user["id"] == BOT_OWNER_ID:
        nav_options.append("User Management")
    page = st.sidebar.radio("Navigation", nav_options)
    
    if page == "Dashboard":
        dashboard_page()
    elif page == "Server Management":
        server_management_page()
    elif page == "User Management":
        user_management_page()

if __name__ == '__main__':
    main()
