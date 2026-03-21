import streamlit as st
import os
from utils.auth import authenticate, logout, check_auth, get_role
from utils.db import init_db

# Page Config
st.set_page_config(
    page_title="Internal Ticketing System",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .stBadge { background-color: #6c757d; color: white; padding: 2px 8px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# Initialize Session State
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None

# Initialize DB
if 'db_initialized' not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

def login_page():
    st.title("🎫 Internal Ticketing System")
    st.subheader("Production-Grade UAT Tracker")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            st.markdown("### Please Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                user = authenticate(username, password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.success(f"Welcome, {username}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

def main_app():
    role = st.session_state.user['role']
    st.sidebar.title(f"Logged in as: {st.session_state.user['username'].capitalize()}")
    st.sidebar.markdown(f"Role: **{role.upper()}**")
    
    if st.sidebar.button("Logout"):
        logout()
    
    st.title(f"Welcome to the {role.capitalize()} Dashboard")
    
    # Dynamic Navigation Info
    if role == 'admin':
        st.markdown("""
        You have full access to:
        - **Report Issue**: Submit new bugs or enhancements.
        - **Dashboard**: Full management and assignment.
        - **Kanban**: Visual status tracking.
        - **Analytics**: Performance insights.
        - **User Management**: Create and manage roles.
        """)
    elif role == 'developer':
        st.markdown("""
        You can view and manage your assigned tasks:
        - **Dashboard**: Filtered to your assigned issues.
        - **Kanban**: Visual progress of your work.
        """)
    elif role == 'reporter':
        st.markdown("""
        You can submit new issues:
        - **Report Issue**: Create new tracking requests.
        """)

if not check_auth():
    login_page()
else:
    main_app()
