import streamlit as st
from utils.auth import require_role
from utils.db import add_issue, get_connection
from utils.helpers import get_priority_color
from utils.drive import upload_file

# Page Config
st.set_page_config(page_title="Report Issue", page_icon="📝", layout="wide")

# Enforce Authentication & Role
require_role(['admin', 'reporter'])

st.title("📝 Report a New Issue")
st.markdown("Fill out the form below to track a bug, enhancement, or feedback.")

with st.form("report_issue_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        title = st.text_input("Title*", placeholder="Brief summary of the issue")
        issue_type = st.selectbox("Type*", ["Bug", "Enhancement", "Feedback"])
        priority = st.select_slider(
            "Priority*", 
            options=["P2", "P1", "P0"], 
            value="P2", 
            help="P0 is highest priority"
        )
        
    with col2:
        module = st.text_input("Module", placeholder="e.g., Auth, Dashboard, API")
        uploaded_file = st.file_uploader(
            "Screenshot / File", 
            type=["png", "jpg", "jpeg", "pdf", "csv", "txt"]
        )
        
    description = st.text_area(
        "Description*", 
        placeholder="Provide details, steps to reproduce, or expected behavior..."
    )
    
    submit = st.form_submit_button("Submit Issue")
    
    if submit:
        if not title or not description or not issue_type:
            st.error("Please fill in all required fields (*)")
        else:
            try:
                # Step 1: Prepare data
                issue_data = {
                    'title': title,
                    'description': description,
                    'type': issue_type,
                    'priority': priority,
                    'module': module,
                    'reporter': st.session_state.user['username']
                }
                
                # Step 2: Insert issue first → get issue_id
                issue_id = add_issue(issue_data)

                # Step 3: Upload file to Cloudinary (if exists)
                file_url = None

                if uploaded_file:
                    # File validation
                    if uploaded_file.size > 5 * 1024 * 1024:
                        st.error("File too large (max 5MB)")
                        st.stop()

                    if uploaded_file.type not in [
                        "image/png", "image/jpeg", "application/pdf", 
                        "text/csv", "text/plain"
                    ]:
                        st.error("Unsupported file type")
                        st.stop()

                    file_url = upload_file(uploaded_file, issue_id)

                # Step 4: Update DB with file_url
                if file_url:
                    conn = get_connection()
                    cursor = conn.cursor()

                    cursor.execute(
                        "UPDATE issues SET file_url = ? WHERE issue_id = ?",
                        (file_url, issue_id)
                    )

                    conn.commit()
                    conn.close()

                # Success message
                st.success(f"Successfully reported issue: **{issue_id}**")
                st.balloons()

            except Exception as e:
                st.error(f"Error submitting issue: {e}")

# Sidebar Info
st.sidebar.markdown("---")
st.sidebar.info("Reporter: " + st.session_state.user['username'])
