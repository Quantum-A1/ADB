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
    fetch_servers_for_user,
    get_user_record
)

# --- Authorization Check ---
user = st.session_state.get("user")
if not user:
    st.error("Please log in.")
    st.stop()
user_record = get_user_record(user["id"])
if not user_record:
    st.error("Your account is not authorized. Please contact an administrator.")
    st.stop()
user["access_level"] = user_record.get("access_level", "user")
st.session_state["user"] = user
# --- End Authorization Check ---

access_level = user.get("access_level", "user")
if access_level == "user":
    server_options = ["All"] + fetch_servers_for_user(user["id"])
else:
    server_options = ["All"] + fetch_servers()

st.header("📊 Real-Time Monitoring & Alerts")

st_autorefresh(interval=60000, key="real_time_monitor")
selected_server = st.selectbox("Select Server", options=server_options)

stats = fetch_stats(selected_server)
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("👤 Total Players", stats["total_players"])
col2.metric("🚩 Flagged Accounts", stats["flagged_accounts"])
col3.metric("👀 Watchlisted Accounts", stats["watchlisted_accounts"])
col4.metric("🛡️ Whitelisted Accounts", stats["whitelisted_accounts"])
col5.metric("💻 Multi Device Accounts", stats["multiple_devices"])

if stats["flagged_accounts"] > 50:
    st.error("Alert: High number of flagged accounts!")

df_trend = fetch_trend_data(selected_server)
if not df_trend.empty:
    df_trend['date'] = pd.to_datetime(df_trend['date'])
    df_trend.set_index('date', inplace=True)
    st.line_chart(df_trend)
else:
    st.write("No trend data available")

st.subheader("Detected Alt Accounts (Grouped by Device)")

alt_accounts = fetch_alt_accounts(selected_server)
if alt_accounts:
    device_groups = {}
    for account in alt_accounts:
        device_id = account.get("device_id")
        if device_id:
            device_groups.setdefault(device_id, []).append(account)
    
    group_max_id = {}
    for device_id, group in device_groups.items():
        ids = [acc.get("id") for acc in group if acc.get("id") is not None]
        group_max_id[device_id] = max(ids) if ids else 0

    sorted_device_ids = sorted(device_groups.keys(), key=lambda d: group_max_id[d], reverse=True)
    items_per_page = 10
    total_pages = (len(sorted_device_ids) + items_per_page - 1) // items_per_page
    page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)
    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page

    for device_id in sorted_device_ids[start_index:end_index]:
        st.write(f"**Device ID:** {device_id}")
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
            st.write("  - 🖥️ Server: ", alt.get('server_name', 'N/A'))
            st.write("  - 📅 First Seen: ", alt.get('first_seen', 'N/A'))
            st.write("  - 🕒 Last Seen: ", alt.get('last_seen', 'N/A'))
            st.write("  - 🆔 Device ID: ", device_id)
            st.write("  - 🆔 Gamertag ID: ", alt.get('gamertag_id', 'N/A'))
        st.write("---")
else:
    st.write("No alt accounts detected.")
