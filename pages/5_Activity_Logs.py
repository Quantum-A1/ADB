# ActivityLogs.py
import streamlit as st
import pandas as pd
import json
from common import fetch_activity_logs

def diff_states(before_json, after_json):
    """
    Given two JSON strings representing before and after states,
    return concise diff summaries for only the fields that changed.
    """
    try:
        before = json.loads(before_json)
        after = json.loads(after_json)
    except Exception as e:
        return before_json, after_json

    diffs_before = []
    diffs_after = []
    # Compare keys from both dictionaries.
    for key in set(before.keys()).union(after.keys()):
        b = before.get(key)
        a = after.get(key)
        if b != a:
            # For boolean flags, show Yes/No
            if key.lower() in ["alt_flag", "watchlisted", "whitelist", "multiple_devices"]:
                b_str = "Yes" if b else "No"
                a_str = "Yes" if a else "No"
            else:
                b_str = str(b)
                a_str = str(a)
            diffs_before.append(f"{key.capitalize()} - {b_str}")
            diffs_after.append(f"{key.capitalize()} - {a_str}")
    return ", ".join(diffs_before), ", ".join(diffs_after)

st.header("Activity Logs & Audit Trail")

# Optional: Add a search/filter bar
search_term = st.text_input("Search Logs", "")
logs = fetch_activity_logs()
df_logs = pd.DataFrame(logs)

# If there are logs, process them.
if not df_logs.empty:
    # If a search term is provided, filter logs.
    if search_term:
        df_logs = df_logs[
            df_logs["user_id"].str.contains(search_term, case=False) |
            df_logs["action"].str.contains(search_term, case=False) |
            df_logs["details"].str.contains(search_term, case=False)
        ]
    
    # Process rows for "Account Edit" to show concise before/after differences.
    for idx, row in df_logs.iterrows():
        if row.get("action") == "Account Edit":
            before, after = diff_states(row.get("before_state", ""), row.get("after_state", ""))
            df_logs.at[idx, "before_state"] = before
            df_logs.at[idx, "after_state"] = after

    st.dataframe(df_logs)
else:
    st.write("No activity logs found.")
