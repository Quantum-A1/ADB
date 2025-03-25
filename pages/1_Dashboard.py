import streamlit as st
import pandas as pd
import plotly.express as px
from common import fetch_stats, fetch_trend_data, fetch_servers, fetch_servers_for_user

user = st.session_state.get("user")
access_level = user.get("access_level", "user")

if access_level == "user":
    # Only fetch servers managed by this user. (Requires your DB to record this info.)
    server_options = ["All"] + fetch_servers_for_user(user["id"])
else:
    server_options = ["All"] + fetch_servers()

st.header("Dashboard")
selected_server = st.selectbox("Select Server (for all stats)", options=server_options)

# Fetch and display stats.
stats = fetch_stats(selected_server)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Players", stats["total_players"])
col2.metric("Flagged Accounts", stats["flagged_accounts"])
col3.metric("Watchlisted Accounts", stats["watchlisted_accounts"])
col4.metric("Whitelisted Accounts", stats["whitelisted_accounts"])

# Pie chart and trends.
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
