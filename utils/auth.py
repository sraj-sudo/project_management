import streamlit as st
import bcrypt
from utils.db import get_user_by_username, verify_password

def authenticate(username, password):
    user = get_user_by_username(username)
    if user and verify_password(password, user['password_hash']):
        return user
    return None

def check_auth():
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        return False
    # Validate session safety
    if 'user' not in st.session_state or not st.session_state.user:
        return False
    return True

def logout():
    st.session_state.authenticated = False
    st.session_state.user = None
    st.rerun()

def get_role():
    if check_auth():
        return st.session_state.user['role']
    return None

def require_role(allowed_roles):
    """
    Page-level guard to prevent unauthorized access via URL.
    """
    if not check_auth():
        st.warning("Please log in to access this page.")
        st.stop()
    
    role = get_role()
    if role not in allowed_roles:
        st.error(f"Access Denied: Your role ({role}) does not have permission to view this page.")
        st.stop()
    return True

# Specific role helpers for UI toggles
def is_admin():
    return get_role() == 'admin'

def is_developer():
    return get_role() == 'developer'

def is_reporter():
    return get_role() == 'reporter'
