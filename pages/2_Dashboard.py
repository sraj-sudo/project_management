import streamlit as st
import pandas as pd
from utils.auth import require_role, is_admin, get_role
from utils.db import get_issues, get_issue_details, update_issue_status, assign_issue, list_users, add_comment
from utils.helpers import get_status_color, get_priority_color, format_timestamp

# Page Config
st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

# Page Guard: Admin and Developer allowed
require_role(['admin', 'developer'])

st.title("📊 Ticket Dashboard")

# Filters
with st.expander("🔍 Filters & Search", expanded=True):
    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
    with col1:
        f_type = st.multiselect("Type", ["Bug", "Enhancement", "Feedback"], default=[])
    with col2:
        f_status = st.multiselect("Status", ["New", "Review", "In Progress", "Testing", "Closed"], default=[])
    with col3:
        f_priority = st.multiselect("Priority", ["P0", "P1", "P2"], default=[])
    with col4:
        f_search = st.text_input("Search (ID or Title)", placeholder="Search...")

# Fetch Data with Role Context
role = get_role()
username = st.session_state.user['username']

filters = {
    'type': f_type[0] if len(f_type) == 1 else None,
    'status': f_status[0] if len(f_status) == 1 else None,
    'priority': f_priority[0] if len(f_priority) == 1 else None,
    'search': f_search
}

# Backend enforcement: Developers only see assigned issues
if role == 'developer':
    issues = get_issues(filters, current_user=username, current_user_role='developer')
else:
    issues = get_issues(filters)

if not issues:
    st.info("No issues found matching the criteria.")
else:
    for issue in issues:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([1, 3, 1, 1, 1])
            with col1:
                st.markdown(f"**{issue['issue_id']}**")
            with col2:
                st.markdown(f"**{issue['title']}**")
                assignee_label = f"| Assigned: {issue['assigned_to']}" if issue['assigned_to'] else "| Unassigned"
                st.caption(f"Reporter: {issue['reporter']} {assignee_label}")
            with col3:
                color = get_status_color(issue['status'])
                st.markdown(f'<span style="background-color: {color}; color: white; padding: 2px 8px; border-radius: 5px;">{issue["status"]}</span>', unsafe_allow_html=True)
            with col4:
                p_color = get_priority_color(issue['priority'])
                st.markdown(f'<span style="color: {p_color}; font-weight: bold;">{issue["priority"]}</span>', unsafe_allow_html=True)
            with col5:
                if st.button("Details", key=f"details_{issue['issue_id']}"):
                    st.session_state.current_issue_id = issue['issue_id']
            st.markdown("---")

# Detail Sidebar Logic (Expanded for Role Enforcement)
if 'current_issue_id' in st.session_state:
    details = get_issue_details(st.session_state.current_issue_id)
    if details:
        st.sidebar.markdown(f"### Ticket: {details['issue_id']}")
        st.sidebar.markdown(f"**Title:** {details['title']}")
        st.sidebar.markdown(f"**Description:** \n {details['description']}")
        
        st.sidebar.markdown("---")
        
        # Status Update Logic
        st.sidebar.subheader("Action Center")
        
        # Determine allowed statuses based on role
        if role == 'admin':
            status_opts = ["New", "Review", "In Progress", "Testing", "Closed"]
        elif role == 'developer':
            # ENFORCED WORKFLOW: New -> In Progress -> Testing -> Closed
            # Current logic in db.py:
            # allowed_transitions = {
            #     'New': ['In Progress'],
            #     'In Progress': ['Testing'],
            #     'Testing': ['Closed', 'In Progress']
            # }
            # We filter visually too:
            cur = details['status']
            if cur == 'New': status_opts = ['New', 'In Progress']
            elif cur == 'In Progress': status_opts = ['In Progress', 'Testing']
            elif cur == 'Testing': status_opts = ['Testing', 'Closed', 'In Progress']
            else: status_opts = [cur]
        else:
            status_opts = [details['status']]
            
        new_status = st.sidebar.selectbox("New Status", status_opts, index=0)
        if st.sidebar.button("Execute Transition", key=f"up_status_{details['issue_id']}"):
            try:
                if update_issue_status(details['issue_id'], new_status, username, role):
                    st.success("Status updated!")
                    st.rerun()
            except Exception as e:
                st.error(str(e))
        
        # Assignment (Admin Only)
        if is_admin():
            st.sidebar.markdown("---")
            users = [u['username'] for u in list_users() if u['role'] in ['admin', 'developer']]
            assignee = st.sidebar.selectbox("Assign To", [""] + users, index=0 if not details['assigned_to'] else users.index(details['assigned_to']) + 1)
            if st.sidebar.button("Save Assignment", key=f"assign_{details['issue_id']}"):
                try:
                    assign_issue(details['issue_id'], assignee if assignee else None, role)
                    st.success(f"Assigned to {assignee}")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        
        # Comments & History
        st.sidebar.markdown("---")
        st.sidebar.markdown("**Discussion**")
        for comment in details['comments']:
            st.sidebar.caption(f"{comment['user']} ({format_timestamp(comment['timestamp'])})")
            st.sidebar.markdown(f"> {comment['text']}")
            
        new_comment = st.sidebar.text_area("Add Comment", key="new_comment")
        if st.sidebar.button("Post"):
            add_comment(details['issue_id'], username, new_comment)
            st.rerun()

        if st.sidebar.checkbox("Audit History"):
            st.sidebar.markdown("**Issue History**")
            for h in details['history']:
                st.sidebar.caption(f"{format_timestamp(h['timestamp'])}: {h['old_status']} ➡️ {h['new_status']} by {h['changed_by']}")

st.sidebar.markdown("---")
if st.sidebar.button("Reset View"):
    if 'current_issue_id' in st.session_state:
        del st.session_state.current_issue_id
        st.rerun()
