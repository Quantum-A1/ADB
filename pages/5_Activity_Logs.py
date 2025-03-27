# ActivityLogs.py
import streamlit as st
import pandas as pd
import json
from common import fetch_activity_logs

def diff_states(before_json, after_json):
    """
    Given two JSON strings representing before and after states,
    return concise diff summaries only for these keys:
    "alt_flag", "watchlisted", "whitelist", and "multiple_devices".
    If the parsed values are not dictionaries, return empty diffs.
    """
    keys_to_check = ["alt_flag", "watchlisted", "whitelist", "multiple_devices"]
    
    try:
        before = json.loads(before_json)
    except Exception:
        before = {}
    try:
        after = json.loads(after_json)
    except Exception:
        after = {}
    
    # If either parsed value is not a dict, return no diff.
    if not isinstance(before, dict) or not isinstance(after, dict):
        return "", ""
    
    diffs_before = []
    diffs_after = []
    for key in keys_to_check:
        if before.get(key) != after.get(key):
            # For boolean flags, show Yes/No
            b = before.get(key)
            a = after.get(key)
            b_str = "Yes" if b else "No"
            a_str = "Yes" if a else "No"
            diffs_before.append(f"{key.capitalize()} - {b_str}")
            diffs_after.append(f"{key.capitalize()} - {a_str}")
    return ", ".join(diffs_before), ", ".join(diffs_after)

st.header("Activity Logs & Audit Trail")

# Optional: Add a search/filter bar
search_term = st.text_input("Search Logs", "")
logs = fetch_activity_logs()
df_logs = pd.DataFrame(logs)

if not df_logs.empty:
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
