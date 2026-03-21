import streamlit as st
from utils.auth import require_role, get_role
from utils.db import get_issues, update_issue_status
from utils.helpers import get_status_color, get_priority_color

# Page Config
st.set_page_config(page_title="Kanban Board", page_icon="🧩", layout="wide")

# Page Guard: Admin and Developer allowed
require_role(['admin', 'developer'])

st.title("🧩 Kanban Board")

# Fetch Context
role = get_role()
username = st.session_state.user['username']

# Fetch Issues (Backend enforcement: Developers only see assigned)
if role == 'developer':
    issues = get_issues(current_user=username, current_user_role='developer')
else:
    issues = get_issues()

# Status Columns
statuses = ["New", "Review", "In Progress", "Testing", "Closed"]
cols = st.columns(len(statuses))

for i, status in enumerate(statuses):
    with cols[i]:
        st.markdown(f"### {status}")
        st.markdown("---")
        
        status_issues = [iss for iss in issues if iss['status'] == status]
        
        if not status_issues:
            st.caption("Empty")
        
        for issue in status_issues:
            with st.expander(f"**{issue['issue_id']}**: {issue['title']}", expanded=True):
                # Priority & Role Badge
                p_color = get_priority_color(issue['priority'])
                st.markdown(f'<span style="background-color: {p_color}; color: white; padding: 1px 5px; border-radius: 5px; font-size: 0.7em;">{issue["priority"]}</span>', unsafe_allow_html=True)
                
                if issue['assigned_to'] == username:
                    st.markdown('<span style="background-color: #28a745; color: white; padding: 1px 5px; border-radius: 5px; font-size: 0.7em;">Assigned To Me</span>', unsafe_allow_html=True)
                
                st.caption(f"Type: {issue['type']}")
                st.caption(f"Reporter: {issue['reporter']}")
                
                # Move Dropdown (Role Restricted)
                if role == 'admin':
                    opts = statuses
                elif role == 'developer':
                    # Role-specific transitions allowed in backend
                    opts = [status, "In Progress", "Testing", "Closed"]
                    opts = list(set(opts)) # dedupe
                else:
                    opts = [status]
                
                new_status = st.selectbox("Action:", opts, index=opts.index(status), key=f"move_{issue['issue_id']}")
                if new_status != status:
                    try:
                        if update_issue_status(issue['issue_id'], new_status, username, role):
                            st.success(f"Moved {issue['issue_id']}")
                            st.rerun()
                    except Exception as e:
                        st.error(str(e))

st.sidebar.markdown("---")
st.sidebar.info("Workflow Enforcement:\nAdmin can move any issue.\nDeveloper can move assigned issues through the pipeline.")
