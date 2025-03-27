# Feedback.py
import streamlit as st
import pandas as pd
import json
from common import add_user_feedback, fetch_feedback, get_user_record

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

st.header("User Feedback & Support")

with st.form("feedback_form", clear_on_submit=True):
    subject = st.text_input("Subject")
    message = st.text_area("Message")
    category = st.selectbox("Category", ["Bug Report", "Feature Request", "General Feedback"])
    priority = st.selectbox("Priority", ["Low", "Medium", "High"])
    submitted = st.form_submit_button("Submit Feedback")
    if submitted:
        if subject and message:
            feedback_details = {
                "subject": subject,
                "message": message,
                "category": category,
                "priority": priority
            }
            add_user_feedback(user["id"], subject, feedback_details)
            st.success("Feedback submitted! Thank you.")
        else:
            st.error("Please fill out both the subject and message.")

# Only display submitted feedback to moderators or higher.
if user.get("access_level") in ["moderator", "admin", "super-admin"]:
    st.subheader("Submitted Feedback")
    feedback_list = fetch_feedback()
    if feedback_list:
        df_feedback = pd.DataFrame(feedback_list)
        st.dataframe(df_feedback)
    else:
        st.write("No feedback submitted yet.")
