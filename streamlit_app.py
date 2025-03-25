import streamlit as st
import pymysql
import pandas as pd
import os
from dotenv import load_dotenv

# Load local .env if running locally
if not st.secrets:
    load_dotenv()

DB_HOST = st.secrets.get("DB_HOST") or os.getenv("DB_HOST")
DB_USER = st.secrets.get("DB_USER") or os.getenv("DB_USER")
DB_PASS = st.secrets.get("DB_PASS") or os.getenv("DB_PASS")
DB_NAME = st.secrets.get("DB_NAME") or os.getenv("DB_NAME")

def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )

# -------------------------------
# Helper function: Get DB connection
# -------------------------------
def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )


# -------------------------------
# Function: Fetch summary statistics
# -------------------------------
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

# -------------------------------
# Function: Fetch alt detection trend data
# -------------------------------
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

# -------------------------------
# Function: Update guild configuration (e.g., update server name)
# -------------------------------
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

# -------------------------------
# Main Dashboard Layout
# -------------------------------
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
        # Set 'date' column as the index for the line chart
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
