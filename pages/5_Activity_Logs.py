# ActivityLogs.py
import streamlit as st
import pandas as pd
from common import fetch_activity_logs

# Check user access level – only allow moderators and above.
user = st.session_state.get("user")
access_level = user.get("access_level", "user")
if access_level not in ["moderator", "admin", "super-admin"]:
    st.error("Access Denied: You must be a moderator or higher to view activity logs.")
    st.stop()

st.header("Activity Logs & Audit Trail")

# Optional: Add a search/filter bar
search_term = st.text_input("Search Logs", "")
logs = fetch_activity_logs()
df_logs = pd.DataFrame(logs)

if not df_logs.empty:
    if search_term:
        # Filter by user_id, action, or details
        df_logs = df_logs[
            df_logs["user_id"].str.contains(search_term, case=False) |
            df_logs["action"].str.contains(search_term, case=False) |
            df_logs["details"].str.contains(search_term, case=False)
        ]
    st.dataframe(df_logs)
else:
    st.write("No activity logs found.")
