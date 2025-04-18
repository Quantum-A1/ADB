# common.py
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

# Load environment variables if needed.
if not st.secrets:
    load_dotenv()

# Global settings from secrets/environment
DB_HOST = st.secrets.get("DB_HOST") or os.getenv("DB_HOST")
DB_USER = st.secrets.get("DB_USER") or os.getenv("DB_USER")
DB_PASS = st.secrets.get("DB_PASS") or os.getenv("DB_PASS")
DB_NAME = st.secrets.get("DB_NAME") or os.getenv("DB_NAME")

DISCORD_CLIENT_ID = st.secrets.get("DISCORD_CLIENT_ID") or os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = st.secrets.get("DISCORD_CLIENT_SECRET") or os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = st.secrets.get("DISCORD_REDIRECT_URI") or os.getenv("DISCORD_REDIRECT_URI")
BOT_OWNER_ID = st.secrets.get("BOT_OWNER_ID") or os.getenv("BOT_OWNER_ID")

DISCORD_OAUTH_URL = "https://discord.com/api/oauth2/authorize"
DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"
DISCORD_API_URL = "https://discord.com/api/users/@me"

# ---------------------------------------------------------------------------
# Database Connection Pooling
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Authentication Helpers (Discord OAuth)
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Database Query Helper Functions
# ---------------------------------------------------------------------------
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

            # New: Query to count accounts using multiple devices.
            multi_query = "SELECT COUNT(*) AS multiple_devices FROM players WHERE multiple_devices = TRUE"
            if server_name and server_name != "All":
                multi_query += " AND LOWER(TRIM(server_name)) LIKE CONCAT('%%', LOWER(TRIM(%s)), '%%')"
                cursor.execute(multi_query, (server_name,))
            else:
                cursor.execute(multi_query)
            multiple_devices = cursor.fetchone()["multiple_devices"]
    finally:
        release_db_connection(conn)

    return {
        "total_players": total_players,
        "flagged_accounts": flagged_accounts,
        "watchlisted_accounts": watchlisted_accounts,
        "whitelisted_accounts": whitelisted_accounts,
        "multiple_devices": multiple_devices
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

# Helpers        

def fetch_server_config(server_name):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM guild_configs WHERE server_name = %s", (server_name,))
            return cursor.fetchone()
    finally:
        release_db_connection(conn)

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

# Add this function to common.py
def get_user_record(discord_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM user_access WHERE discord_id = %s", (discord_id,))
            return cursor.fetchone()
    finally:
        release_db_connection(conn)

def fetch_servers_for_user(discord_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            query = "SELECT DISTINCT server_name FROM user_servers WHERE discord_id = %s"
            cursor.execute(query, (discord_id,))
            rows = cursor.fetchall()
            return [row["server_name"] for row in rows if row["server_name"]]
    finally:
        release_db_connection(conn)


def update_user_access(discord_id, new_username, new_access):
    """
    Updates the username and access level for the user with the given Discord ID.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            query = """
            UPDATE user_access
            SET username = %s, access_level = %s
            WHERE discord_id = %s
            """
            cursor.execute(query, (new_username, new_access, discord_id))
            conn.commit()
            st.success("User updated successfully.")
    except Exception as e:
        st.error(f"Error updating user: {e}")
    finally:
        release_db_connection(conn)

def remove_user_by_discord_id(discord_id):
    """
    Removes a user from the user_access table and deletes associated server assignments.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # First remove assignments from the user_servers table
            cursor.execute("DELETE FROM user_servers WHERE discord_id = %s", (discord_id,))
            # Then remove the user from the user_access table
            cursor.execute("DELETE FROM user_access WHERE discord_id = %s", (discord_id,))
            conn.commit()
    except Exception as e:
        st.error(f"Error removing user: {e}")
    finally:
        release_db_connection(conn)

def assign_servers_to_user(discord_id, server_list):
    """
    Assigns the provided list of servers to the user with the given discord_id.
    Existing assignments are removed first.
    Assumes you have a table 'user_servers' with columns 'discord_id' and 'server_name'.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Remove current assignments for the given user
            cursor.execute("DELETE FROM user_servers WHERE discord_id = %s", (discord_id,))
            # Insert new assignments
            for server in server_list:
                cursor.execute(
                    "INSERT INTO user_servers (discord_id, server_name) VALUES (%s, %s)",
                    (discord_id, server)
                )
            conn.commit()
            st.success("Server assignments updated successfully.")
    except Exception as e:
        st.error(f"Error updating server assignments: {e}")
    finally:
        release_db_connection(conn)

def get_assigned_servers_for_user(discord_id):
    """
    Retrieves the list of server names assigned to the user with the given discord_id.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT server_name FROM user_servers WHERE discord_id = %s", (discord_id,))
            rows = cursor.fetchall()
            return [row["server_name"] for row in rows]
    finally:
        release_db_connection(conn)


def log_activity(user_id, action, details, before_state, after_state):
    """
    Logs an activity with details including before and after states.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            query = """
                INSERT INTO activity_logs (user_id, action, details, before_state, after_state, timestamp)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """
            cursor.execute(query, (user_id, action, details, before_state, after_state))
            conn.commit()
    finally:
        release_db_connection(conn)


def fetch_activity_logs():
    """Fetches all activity logs ordered by the most recent."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM activity_logs ORDER BY timestamp DESC")
            logs = cursor.fetchall()
    finally:
        release_db_connection(conn)
    return logs


def add_user_feedback(user_id, subject, message, category, priority):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            query = """
            INSERT INTO user_feedback (user_id, subject, message, category, priority, timestamp)
            VALUES (%s, %s, %s, %s, %s, NOW())
            """
            cursor.execute(query, (user_id, subject, message, category, priority))
            conn.commit()
    finally:
        release_db_connection(conn)


def fetch_feedback():
    """Fetch all feedback entries."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM user_feedback ORDER BY timestamp DESC")
            feedback = cursor.fetchall()
    finally:
        release_db_connection(conn)
    return feedback

def fetch_alt_accounts(server_name=None):
    """Fetches accounts flagged as alt accounts, optionally filtering by server."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            query = "SELECT * FROM players WHERE alt_flag = TRUE"
            if server_name and server_name != "All":
                query += " AND LOWER(TRIM(server_name)) LIKE CONCAT('%%', LOWER(TRIM(%s)), '%%')"
                cursor.execute(query, (server_name,))
            else:
                cursor.execute(query)
            rows = cursor.fetchall()
    finally:
        release_db_connection(conn)
    return rows

def fetch_all_accounts():
    """Fetches all accounts from the players table."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            query = "SELECT * FROM players ORDER BY id DESC"
            cursor.execute(query)
            rows = cursor.fetchall()
    finally:
        release_db_connection(conn)
    return rows

def update_account_details(account_id, new_gamertag, alt_flag, watchlisted, whitelist, multiple_devices):
    """Updates account details in the players table using the 'gamertag' column."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            query = """
                UPDATE players
                SET gamertag = %s,
                    alt_flag = %s,
                    watchlisted = %s,
                    whitelist = %s,
                    multiple_devices = %s
                WHERE id = %s
            """
            cursor.execute(query, (new_gamertag, alt_flag, watchlisted, whitelist, multiple_devices, account_id))
            conn.commit()
    finally:
        release_db_connection(conn)

        
def fetch_main_account_by_device(device_id):
    """Fetch the main account (without an alt flag) for a given device_id."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            query = "SELECT * FROM players WHERE device_id = %s AND alt_flag = FALSE LIMIT 1"
            cursor.execute(query, (device_id,))
            main_account = cursor.fetchone()
    finally:
        release_db_connection(conn)
    return main_account
