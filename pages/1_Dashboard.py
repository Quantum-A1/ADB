import streamlit as st
import pandas as pd
import plotly.express as px
from common import fetch_stats, fetch_trend_data, fetch_servers, fetch_servers_for_user

user = st.session_state.get("user")
access_level = user.get("access_level", "user")

# For regular users, display only assigned servers.
# For any user with admin-level permissions or higher, show all servers.
if access_level == "user":
    server_options = ["All"] + fetch_servers_for_user(user["id"])
else:
    server_options = ["All"] + fetch_servers()

st.header("🏠 Dashboard")
st.sidebar.subheader("Customize Dashboard")
selected_metrics = st.sidebar.multiselect(
    "Select metrics to display",
    options=[
        "Total Players", 
        "Flagged Accounts", 
        "Watchlisted Accounts", 
        "Whitelisted Accounts",
        "Multi Device Accounts"  # Option label remains; underlying key will be 'multiple_devices'
    ],
    default=[
        "Total Players", 
        "Flagged Accounts", 
        "Watchlisted Accounts", 
        "Whitelisted Accounts",
        "Multi Device Accounts"
    ]
)

selected_server = st.selectbox("Select Server (for all stats)", options=server_options)

# Fetch and display stats.
stats = fetch_stats(selected_server)
# Create columns dynamically based on the number of selected metrics
num_metrics = len(selected_metrics)
columns = st.columns(num_metrics)
for idx, metric in enumerate(selected_metrics):
    if metric == "Total Players":
        columns[idx].metric("👤 Total Players", stats["total_players"])
    elif metric == "Flagged Accounts":
        columns[idx].metric("🚩 Flagged Accounts", stats["flagged_accounts"])
    elif metric == "Watchlisted Accounts":
        columns[idx].metric("👀 Watchlisted Accounts", stats["watchlisted_accounts"])
    elif metric == "Whitelisted Accounts":
        columns[idx].metric("🛡️ Whitelisted Accounts", stats["whitelisted_accounts"])
    elif metric == "Multi Device Accounts":
        columns[idx].metric("💻 Multi Device Accounts", stats.get("multiple_devices", 0))

# Pie chart and trends.
summary_df = pd.DataFrame({
    "Metric": [
        "Flagged Accounts", 
        "Watchlisted Accounts", 
        "Whitelisted Accounts",
        "Multi Device Accounts"
    ],
    "Value": [
        stats["flagged_accounts"], 
        stats["watchlisted_accounts"], 
        stats["whitelisted_accounts"],
        stats.get("multiple_devices", 0)
    ]
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
