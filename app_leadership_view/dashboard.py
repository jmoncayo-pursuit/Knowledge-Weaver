"""
Knowledge-Weaver Leadership Dashboard
Streamlit application for leadership metrics and insights
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

from api_client import APIClient

# Page configuration
st.set_page_config(
    page_title="Knowledge-Weaver Leadership Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load custom CSS
def load_css():
    try:
        with open('styles/dark_theme.css') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        pass  # CSS file not found, use default styling

load_css()

# Initialize API client
@st.cache_resource
def get_api_client():
    return APIClient()

api_client = get_api_client()

# Auto-refresh every 60 seconds
st_autorefresh = st.empty()
with st_autorefresh:
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • Auto-refresh: 60s")

# Title
st.markdown('<h1 class="dashboard-title">Knowledge-Weaver Leadership Dashboard</h1>', unsafe_allow_html=True)
st.markdown('<p class="dashboard-subtitle">Monitor team performance and knowledge gaps</p>', unsafe_allow_html=True)

# Metrics functions
def render_response_time_metric():
    """Render average leadership response time metric"""
    # Placeholder implementation
    response_time = "1h 15m"
    delta = "-15m"
    
    st.metric(
        label="Avg Response Time",
        value=response_time,
        delta=delta,
        help="Average time for leadership to respond to agent questions"
    )

def render_query_volume_metric():
    """Render query volume metric from last 7 days"""
    try:
        # Fetch query logs from last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        logs = api_client.fetch_query_logs(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            limit=1000
        )
        
        query_count = len(logs)
        
        # Calculate delta (placeholder - would need historical data)
        delta = "+15%"
        
        st.metric(
            label="Query Volume (7d)",
            value=f"{query_count:,}",
            delta=delta,
            help="Total queries in the last 7 days"
        )
    except Exception as e:
        st.metric(
            label="Query Volume (7d)",
            value="Error",
            help=f"Failed to fetch data: {str(e)}"
        )

def render_knowledge_gap_metric():
    """Render knowledge gaps metric"""
    # Placeholder implementation
    gap_count = 8
    delta = "-2"
    
    st.metric(
        label="Knowledge Gaps",
        value=gap_count,
        delta=delta,
        help="Queries with no relevant results found"
    )

# Render metrics
col1, col2, col3 = st.columns(3)

with col1:
    render_response_time_metric()

with col2:
    render_query_volume_metric()

with col3:
    render_knowledge_gap_metric()

# Unanswered Questions Section
st.markdown("---")
st.subheader("Unanswered Questions")

try:
    unanswered = api_client.fetch_unanswered_questions()
    
    if unanswered and len(unanswered) > 0:
        # Create DataFrame from unanswered questions
        df = pd.DataFrame(unanswered)
        
        # Filter to only show questions older than 24 hours
        if 'age_hours' in df.columns:
            df_filtered = df[df['age_hours'] >= 24].copy()
        else:
            # If age_hours not in data, show all
            df_filtered = df.copy()
        
        if len(df_filtered) > 0:
            # Sort by age (oldest first)
            if 'age_hours' in df_filtered.columns:
                df_filtered = df_filtered.sort_values('age_hours', ascending=False)
            
            # Display top 20
            df_display = df_filtered.head(20)
            
            # Format columns for display
            display_columns = []
            if 'question_text' in df_display.columns:
                display_columns.append('question_text')
            if 'agent' in df_display.columns:
                display_columns.append('agent')
            if 'age_hours' in df_display.columns:
                # Format age_hours to be more readable
                df_display['age_hours'] = df_display['age_hours'].apply(lambda x: f"{x:.1f}h")
                display_columns.append('age_hours')
            if 'timestamp' in df_display.columns:
                display_columns.append('timestamp')
            
            # Display the dataframe
            if display_columns:
                st.dataframe(
                    df_display[display_columns],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            st.caption(f"Showing {len(df_display)} of {len(df_filtered)} unanswered questions (older than 24 hours)")
        else:
            st.info("No unanswered questions older than 24 hours")
    else:
        st.info("No unanswered questions at this time")
except Exception as e:
    st.warning(f"Unable to fetch unanswered questions: {str(e)}")

# Trending Topics Section
st.markdown("---")
st.subheader("Trending Topics")

try:
    # Fetch query logs from last 7 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    logs = api_client.fetch_query_logs(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        limit=1000
    )
    
    if logs and len(logs) > 0:
        # Extract query texts
        queries = [log.get('query_text', '') for log in logs if log.get('query_text')]
        
        if queries:
            # Simple keyword extraction - extract first 3-5 words as "topic"
            topics = []
            for query in queries:
                # Take first 50 characters as topic (simple approach for hackathon)
                words = query.split()[:5]  # First 5 words
                topic = ' '.join(words)
                if topic:
                    topics.append(topic)
            
            if topics:
                # Create DataFrame and get value counts
                df_topics = pd.DataFrame({'topic': topics})
                topic_counts = df_topics['topic'].value_counts().head(10)
                
                # Display as bar chart
                st.bar_chart(topic_counts)
                
                # Also show as table
                st.caption("Top 10 Most Frequent Query Topics (Last 7 Days)")
                topic_df = pd.DataFrame({
                    'Topic': topic_counts.index,
                    'Count': topic_counts.values
                })
                st.dataframe(topic_df, use_container_width=True, hide_index=True)
            else:
                st.info("No topics extracted from queries")
        else:
            st.info("No query data available for analysis")
    else:
        st.info("No query logs available for trending topics analysis")
except Exception as e:
    st.warning(f"Unable to analyze trending topics: {str(e)}")

# Backend connection status
with st.sidebar:
    st.subheader("Backend Status")
    if api_client.test_connection():
        st.success("✓ Connected to backend")
    else:
        st.error("✗ Backend unavailable")
    
    if st.button("Refresh Dashboard"):
        st.rerun()

# Auto-refresh after 60 seconds
time.sleep(60)
st.rerun()
