# RealTimeMonitoring.py
import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
from common import fetch_stats, fetch_trend_data, fetch_alt_accounts

st.header("Real-Time Monitoring & Alerts")

# Auto-refresh every 60 seconds
st_autorefresh(interval=60000, key="real_time_monitor")

# Allow the user to select a server if needed
server_options = ["All"]  # You can extend this by fetching servers as in your Dashboard
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

# --- New Section: List Detected Alt Accounts ---
st.subheader("Detected Alt Accounts")
alt_accounts = fetch_alt_accounts(selected_server)
if alt_accounts:
    # Display each alt account as a list item.
    for account in alt_accounts:
        st.write(f"{account.get('username', 'N/A')} - Server: {account.get('server_name', 'N/A')}")
else:
    st.write("No alt accounts detected.")
