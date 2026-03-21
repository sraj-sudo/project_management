import streamlit as st
from utils.auth import require_role, is_admin
from utils.db import create_user, list_users

# Page Config
st.set_page_config(page_title="User Management", page_icon="👥", layout="wide")

# Page Guard: Only Admin allowed
require_role(['admin'])

st.title("👥 User Management")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Add New User")
    with st.form("add_user_form", clear_on_submit=True):
        username = st.text_input("Username*")
        password = st.text_input("Password*", type="password")
        role = st.selectbox("Role*", ["admin", "developer", "reporter"], index=2)
        submit = st.form_submit_button("Create User")
        
        if submit:
            if not username or not password:
                st.error("Username and password are required.")
            else:
                success = create_user(username, password, role, st.session_state.user['role'])
                if success:
                    st.success(f"User '{username}' created successfully!")
                    st.rerun()
                else:
                    st.error("User creation failed. Username might already exist.")

with col2:
    st.subheader("Existing Users")
    users = list_users()
    if users:
        import pandas as pd
        df = pd.DataFrame(users)
        st.table(df)
    else:
        st.info("No users found.")

st.sidebar.markdown("---")
st.sidebar.info("Admin Control: Manage system access and roles.")
