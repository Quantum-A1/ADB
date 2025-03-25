import streamlit as st
import pymysql
import pandas as pd
import os
from dotenv import load_dotenv
import requests
from urllib.parse import urlencode

# ------------------------------------------------------------------------------
# Authentication via Discord OAuth
# ------------------------------------------------------------------------------

# Load local .env if running locally
if not st.secrets:
    load_dotenv()

# Initialize session state for user if not already set
if "user" not in st.session_state:
    st.session_state["user"] = None

# Load DB credentials and Discord OAuth credentials from st.secrets (or .env)
DB_HOST = st.secrets.get("DB_HOST") or os.getenv("DB_HOST")
DB_USER = st.secrets.get("DB_USER") or os.getenv("DB_USER")
DB_PASS = st.secrets.get("DB_PASS") or os.getenv("DB_PASS")
DB_NAME = st.secrets.get("DB_NAME") or os.getenv("DB_NAME")

DISCORD_CLIENT_ID = st.secrets.get("DISCORD_CLIENT_ID") or os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = st.secrets.get("DISCORD_CLIENT_SECRET") or os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = st.secrets.get("DISCORD_REDIRECT_URI") or os.getenv("DISCORD_REDIRECT_URI")

# Discord OAuth endpoints
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
        "redirect_uri": DISCORD_REDIRECT_URI,
        # "scope": "identify email"  # Remove this line
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    response = requests.post(DISCORD_TOKEN_URL, data=data, headers=headers)
    response.raise_for_status()
    return response.json()


def fetch_user_info(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(DISCORD_API_URL, headers=headers)
    response.raise_for_status()
    return response.json()

# Check if the user is already logged in
if st.session_state["user"] is None:
    query_params = st.query_params  # Updated API call
    if "code" in query_params:
        code = query_params["code"][0]
        try:
            token_data = exchange_code_for_token(code)
            user_info = fetch_user_info(token_data["access_token"])
            st.session_state["user"] = user_info
            # Clear the URL query parameters to avoid reprocessing
            st.set_query_params()  # Updated API call
        except Exception as e:
            st.error(f"Authentication failed: {e}")
            st.stop()
    else:
        st.write("Please log in to access the dashboard.")
        login_with_discord()
        st.stop()

# Use a safe retrieval for user info before displaying welcome message
user = st.session_state.get("user")
if not user:
    st.error("User information is missing. Please log in.")
    st.stop()
st.write(f"Welcome, **{user['username']}**!")

# ------------------------------------------------------------------------------
# User Management: Allow only specific Discord users to access the dashboard
# ------------------------------------------------------------------------------
allowed_ids = st.secrets.get("ALLOWED_DISCORD_IDS", "").split(",")
allowed_ids = [uid.strip() for uid in allowed_ids if uid.strip()]
if user["id"] not in allowed_ids:
    st.error("Access Denied: You are not authorized to view this dashboard.")
    st.stop()

# ------------------------------------------------------------------------------
# Database Connection and Helper Functions
# ------------------------------------------------------------------------------

def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )

def fetch_stats():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total_players FROM players")
            total_players = cursor.fetchone()["total_players"]

            cursor.execute("SELECT COUNT(*) AS flagged_accounts FROM players WHERE alt_flag = TRUE")
            flagged_accounts = cursor.fetchone()["flagged_accounts"]

            cursor.execute("SELECT COUNT(*) AS watchlisted_accounts FROM players WHERE watchlisted = TRUE")
            watchlisted_accounts = cursor.fetchone()["watchlisted_accounts"]

            cursor.execute("SELECT COUNT(*) AS whitelisted_accounts FROM players WHERE whitelist = TRUE")
            whitelisted_accounts = cursor.fetchone()["whitelisted_accounts"]
    finally:
        conn.close()

    return {
        "total_players": total_players,
        "flagged_accounts": flagged_accounts,
        "watchlisted_accounts": watchlisted_accounts,
        "whitelisted_accounts": whitelisted_accounts
    }

def fetch_trend_data():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT DATE(timestamp) AS date, COUNT(*) AS count
                FROM player_history
                GROUP BY DATE(timestamp)
                ORDER BY date ASC
            """)
            rows = cursor.fetchall()
    finally:
        conn.close()

    return pd.DataFrame(rows)

def update_guild_config(guild_id, new_server_name):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE guild_configs SET server_name = %s WHERE guild_id = %s
            """, (new_server_name, guild_id))
            conn.commit()
    except Exception as e:
        st.error(f"Error updating config: {e}")
    finally:
        conn.close()

# ------------------------------------------------------------------------------
# Main Dashboard Layout
# ------------------------------------------------------------------------------

def main():
    st.title("Alt Detection Dashboard")

    # Summary Statistics Section
    st.header("Summary Statistics")
    stats = fetch_stats()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Players", stats["total_players"])
    col2.metric("Flagged Accounts", stats["flagged_accounts"])
    col3.metric("Watchlisted Accounts", stats["watchlisted_accounts"])
    col4.metric("Whitelisted Accounts", stats["whitelisted_accounts"])

    # Alt Detection Trends Section
    st.header("Alt Detection Trends")
    df_trend = fetch_trend_data()
    if not df_trend.empty:
        df_trend['date'] = pd.to_datetime(df_trend['date'])
        df_trend.set_index('date', inplace=True)
        st.line_chart(df_trend)
    else:
        st.write("No trend data available")

    # Guild Configuration Management Section
    st.header("Manage Guild Configurations")
    with st.form("guild_config_form"):
        guild_id = st.text_input("Guild ID", help="Enter the guild ID")
        new_server_name = st.text_input("New Server Name", help="Enter the new server name")
        submitted = st.form_submit_button("Update Configuration")
        if submitted:
            if guild_id and new_server_name:
                update_guild_config(guild_id, new_server_name)
                st.success("Guild configuration updated!")
            else:
                st.error("Please provide both Guild ID and New Server Name.")

if __name__ == '__main__':
    main()
