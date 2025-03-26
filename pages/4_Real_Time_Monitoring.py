# RealTimeMonitoring.py
import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
from common import (
    fetch_stats,
    fetch_trend_data,
    fetch_alt_accounts,
    fetch_main_account_by_device,
    fetch_servers,
    fetch_servers_for_user
)

user = st.session_state.get("user")
access_level = user.get("access_level", "user")

st.header("📊 Real-Time Monitoring & Alerts")

# Auto-refresh every 60 seconds
st_autorefresh(interval=60000, key="real_time_monitor")

# Determine allowed servers for this user.
if access_level == "user":
    server_options = ["All"] + fetch_servers_for_user(user["id"])
else:
    server_options = ["All"] + fetch_servers()

selected_server = st.selectbox("Select Server", options=server_options)

# Fetch live stats
stats = fetch_stats(selected_server)

# Display metrics
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("👤 Total Players", stats["total_players"])
col2.metric("🚩 Flagged Accounts", stats["flagged_accounts"])
col3.metric("👀 Watchlisted Accounts", stats["watchlisted_accounts"])
col4.metric("🛡️ Whitelisted Accounts", stats["whitelisted_accounts"])
col5.metric("💻 Multi Device Accounts", stats["multiple_devices"])

# Trigger an alert if flagged accounts exceed a threshold (example: 50)
if stats["flagged_accounts"] > 50:
    st.error("Alert: High number of flagged accounts!")

# Display a trend chart
df_trend = fetch_trend_data(selected_server)
if not df_trend.empty:
    df_trend['date'] = pd.to_datetime(df_trend['date'])
    df_trend.set_index('date', inplace=True)
    st.line_chart(df_trend)
else:
    st.write("No trend data available")

# --- New Section: List Detected Alt Accounts Grouped by Device ID with Pagination ---
st.subheader("Detected Alt Accounts (Grouped by Device)")

alt_accounts = fetch_alt_accounts(selected_server)

if alt_accounts:
    # Group alt accounts by device_id
    device_groups = {}
    for account in alt_accounts:
        device_id = account.get("device_id")
        if device_id:
            device_groups.setdefault(device_id, []).append(account)
    
    # For each device group, determine the maximum alt account ID
    group_max_id = {}
    for device_id, group in device_groups.items():
        ids = [acc.get("id") for acc in group if acc.get("id") is not None]
        group_max_id[device_id] = max(ids) if ids else 0

    # Sort device groups in descending order (most recent alt account first)
    sorted_device_ids = sorted(device_groups.keys(), key=lambda d: group_max_id[d], reverse=True)

    # Pagination: Display 10 device groups per page.
    items_per_page = 10
    total_pages = (len(sorted_device_ids) + items_per_page - 1) // items_per_page
    page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)
    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page

    # Display groups for the current page in a list view
    for device_id in sorted_device_ids[start_index:end_index]:
        # Get the main account (account with the same device_id and alt_flag False)
        main_account = fetch_main_account_by_device(device_id)
        if main_account:
            st.write("**👑 Main Account:**")
            st.write("- 📛 Gamertag: ", main_account.get('gamertag', 'N/A'))
            st.write("- 🖥️ Server: ", main_account.get('server_name', 'N/A'))
            st.write("- 📅 First Seen: ", main_account.get('first_seen', 'N/A'))
            st.write("- 🕒 Last Seen: ", main_account.get('last_seen', 'N/A'))
            st.write("- 🆔 Device ID: ", device_id)
            st.write("- 🆔 Gamertag ID: ", main_account.get('gamertag_id', 'N/A'))
        else:
            st.write("**Main Account:** Not found for device_id", device_id)
        
        st.write("**🔗 Alt Accounts:**")
        for alt in device_groups[device_id]:
            st.write("- 📛 Gamertag: ", alt.get('gamertag', 'N/A'))
            st.write("-  🖥️ Server: ", alt.get('server_name', 'N/A'))
            st.write("-  📅 First Seen: ", alt.get('first_seen', 'N/A'))
            st.write("-  🕒 Last Seen: ", alt.get('last_seen', 'N/A'))
            st.write("-  🆔 Device ID: ", device_id)
            st.write("-  🆔 Gamertag ID: ", alt.get('gamertag_id', 'N/A'))
        st.write("---")
else:
    st.write("No alt accounts detected.")
