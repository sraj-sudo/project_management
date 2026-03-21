import streamlit as st
from datetime import datetime
import os

def get_status_color(status):
    colors = {
        'New': 'blue',
        'Review': 'orange',
        'In Progress': 'yellow',
        'Testing': 'purple',
        'Closed': 'green',
        'Fixed': 'green'
    }
    return colors.get(status, 'grey')

def get_priority_color(priority):
    colors = {
        'P0': 'red',
        'P1': 'orange',
        'P2': 'blue'
    }
    return colors.get(priority, 'grey')

def format_timestamp(ts):
    if not ts:
        return "-"
    try:
        dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d %b, %H:%M")
    except:
        return ts

def save_uploaded_file(uploaded_file, issue_id):
    if uploaded_file is not None:
        # {issue_id}_{timestamp}.{ext}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = os.path.splitext(uploaded_file.name)[1]
        filename = f"{issue_id}_{timestamp}{ext}"
        
        upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
            
        file_path = os.path.join(upload_dir, filename)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    return None

def display_badge(text, color):
    st.markdown(f'<span style="background-color: {color}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.8em; margin-right: 5px;">{text}</span>', unsafe_allow_html=True)
