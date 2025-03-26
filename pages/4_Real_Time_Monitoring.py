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
    fetch_servers  # New: Fetch available servers
)

st.header("Real-Time Monitoring & Alerts")

# Auto-refresh every 60 seconds
st_autorefresh(interval=60000, key="real_time_monitor")

# Allow the user to select a server by fetching available servers
server_options = ["All"] + fetch_servers()  # Now includes servers from the DB
selected_server = st.selectbox("Select Server", options=server_options)

# Fetch live stats
stats = fetch_stats(selected_server)

# Display metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Players", stats["total_players"])
col2.metric("Flagged Accounts", stats["flagged_accounts"])
col3.metric("Watchlisted Accounts", stats["watchlisted_accounts"])
col4.metric("Whitelisted Accounts", stats["whitelisted_accounts"])

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
    
    # Pagination: Display 10 device groups per page.
    device_ids = list(device_groups.keys())
    device_ids.sort()
    items_per_page = 10
    total_pages = (len(device_ids) + items_per_page - 1) // items_per_page
    
    # Page selection widget
    page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)
    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page

    # Display groups for the current page
    for device_id in device_ids[start_index:end_index]:
        # Get the main account (account with the same device_id and alt_flag False)
        main_account = fetch_main_account_by_device(device_id)
        if main_account:
            st.write(f"**Main Account:** {main_account.get('gamertag', 'N/A')} - Server: {main_account.get('server_name', 'N/A')}")
        else:
            st.write("**Main Account:** Not found for device_id " + str(device_id))
        
        # List the alt accounts in this group
        for alt in device_groups[device_id]:
            st.write(f"   - **Alt Account:** {alt.get('gamertag', 'N/A')} - Server: {alt.get('server_name', 'N/A')}")
        st.write("---")
else:
    st.write("No alt accounts detected.")
