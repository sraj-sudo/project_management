import streamlit as st
import pandas as pd
import plotly.express as px
from utils.auth import require_role
from utils.db import get_issues
import io

# Page Config
st.set_page_config(page_title="Analytics", page_icon="📈", layout="wide")

# Enforce Authentication: Only Admin
require_role(['admin'])

st.title("📈 Analytics Dashboard")

# Fetch Data
issues = get_issues()

if not issues:
    st.info("No data available to generate charts.")
else:
    df = pd.DataFrame(issues)
    
    # Overview Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Issues", len(df))
    m2.metric("New Issues", len(df[df['status'] == 'New']))
    m3.metric("In Progress", len(df[df['status'] == 'In Progress']))
    m4.metric("Closed", len(df[df['status'] == 'Closed']))
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Issues by Status")
        fig_status = px.pie(df, names='status', color='status', 
                          color_discrete_map={'New': 'blue', 'Review': 'orange', 'In Progress': 'yellow', 'Testing': 'purple', 'Closed': 'green'})
        st.plotly_chart(fig_status, use_container_width=True)
        
    with col2:
        st.subheader("Issues by Priority")
        fig_priority = px.bar(df.groupby('priority').size().reset_index(name='count'), 
                            x='priority', y='count', color='priority',
                            color_discrete_map={'P0': 'red', 'P1': 'orange', 'P2': 'blue'})
        st.plotly_chart(fig_priority, use_container_width=True)
        
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("Issues by Type")
        fig_type = px.pie(df, names='type', hole=0.3)
        st.plotly_chart(fig_type, use_container_width=True)
        
    with col4:
        st.subheader("Daily Issue Trend")
        df['date'] = pd.to_datetime(df['created_at']).dt.date
        trend_df = df.groupby('date').size().reset_index(name='count')
        fig_trend = px.line(trend_df, x='date', y='count', markers=True)
        st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("---")
    
    # Export Section
    st.subheader("📤 Export Data")
    
    # CSV Export
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "Download All Issues as CSV",
        csv,
        "ticketing_system_export.csv",
        "text/csv",
        key='download-csv'
    )

st.sidebar.markdown("---")
st.sidebar.info("Visual insights into performance and issue distribution.")
