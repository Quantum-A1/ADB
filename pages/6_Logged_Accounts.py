# LoggedAccounts.py
import streamlit as st
import pandas as pd
from common import fetch_all_accounts, update_account_details, fetch_servers, fetch_servers_for_user

user = st.session_state.get("user")
access_level = user.get("access_level", "user")

# Determine allowed servers for this user.
if access_level == "user":
    allowed_servers = fetch_servers_for_user(user["id"])
else:
    allowed_servers = fetch_servers()

st.header("📝 Logged Accounts")

# Search bar to filter on gamertag or device_id
search_term = st.text_input("Search Logged Accounts (Gamertag or Device ID)", "")

st.markdown("#### 🔎 Filter by Flags")
# Arrange the flag checkboxes in a row using st.columns.
cols = st.columns(4)
filter_alt = cols[0].checkbox("Alt Accounts", value=False)
filter_watchlisted = cols[1].checkbox("Watchlisted", value=False)
filter_whitelisted = cols[2].checkbox("Whitelisted", value=False)
filter_multiple = cols[3].checkbox("Multiple Device Accounts", value=False)

# Fetch all logged accounts
accounts = fetch_all_accounts()
df_accounts = pd.DataFrame(accounts)

if not df_accounts.empty:
    # Filter by allowed servers
    df_accounts = df_accounts[df_accounts["server_name"].isin(allowed_servers)]

    # Apply search filtering on gamertag or device_id
    if search_term:
        df_accounts = df_accounts[
            df_accounts["gamertag"].str.contains(search_term, case=False, na=False) |
            df_accounts["device_id"].str.contains(search_term, case=False, na=False)
        ]

    # Apply flag filters (only show accounts that meet ALL checked conditions)
    if filter_alt:
        df_accounts = df_accounts[df_accounts["alt_flag"] == True]
    if filter_watchlisted:
        df_accounts = df_accounts[df_accounts["watchlisted"] == True]
    if filter_whitelisted:
        df_accounts = df_accounts[df_accounts["whitelist"] == True]
    if filter_multiple:
        df_accounts = df_accounts[df_accounts["multiple_devices"] == True]

# Display the filtered accounts table
if not df_accounts.empty:
    st.dataframe(df_accounts)
else:
    st.write("No logged accounts found for the selected filters.")

# --- Edit Account Section ---
st.subheader("📋 Edit Account")
if not df_accounts.empty:
    # Build dropdown options based on account id and descriptive text.
    account_options = df_accounts.apply(
        lambda row: (
            row["id"],
            f"{row['gamertag']} - Server: {row['server_name']}"
        ), axis=1
    ).tolist()
    selected_account_id = st.selectbox(
        "Select an account to edit",
        options=[opt[0] for opt in account_options],
        format_func=lambda x: next((opt[1] for opt in account_options if opt[0] == x), str(x))
    )
    # Retrieve the selected account details
    selected_account = df_accounts[df_accounts["id"] == selected_account_id].iloc[0]
    
    with st.form("edit_account_form", clear_on_submit=True):
        new_gamertag = st.text_input("Gamertag", value=selected_account.get("gamertag", ""))
        alt_flag = st.checkbox("Alt Account", value=selected_account.get("alt_flag", False))
        watchlisted = st.checkbox("Watchlisted", value=selected_account.get("watchlisted", False))
        whitelist = st.checkbox("Whitelisted", value=selected_account.get("whitelist", False))
        multiple_devices = st.checkbox("Multiple Device Accounts", value=selected_account.get("multiple_devices", False))
        
        submit_account_edit = st.form_submit_button("Update Account")
        if submit_account_edit:
            update_account_details(selected_account_id, new_gamertag, alt_flag, watchlisted, whitelist, multiple_devices)
            st.success("Account updated successfully.")
else:
    st.write("No account available for editing.")
