# Feedback.py
import streamlit as st
import pandas as pd
from common import add_user_feedback, fetch_feedback

st.header("User Feedback & Support")

# Feedback submission form
with st.form("feedback_form", clear_on_submit=True):
    subject = st.text_input("Subject")
    message = st.text_area("Message")
    submitted = st.form_submit_button("Submit Feedback")
    if submitted:
        if subject and message:
            user = st.session_state.get("user")
            add_user_feedback(user["id"], subject, message)
            st.success("Feedback submitted! Thank you.")
        else:
            st.error("Please fill out both the subject and message.")

# Optionally display feedback to support/moderator/admin users
user = st.session_state.get("user")
if user and user.get("access_level") in ["moderator", "admin", "super-admin"]:
    st.subheader("Submitted Feedback")
    feedback_list = fetch_feedback()
    if feedback_list:
        df_feedback = pd.DataFrame(feedback_list)
        st.dataframe(df_feedback)
    else:
        st.write("No feedback submitted yet.")
