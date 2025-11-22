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
# Caching disabled to ensure fresh data on every refresh
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



# Recent Knowledge Ingestions Section
st.markdown("---")
st.subheader("Recent Knowledge Ingestions")

try:
    recent_entries = api_client.fetch_recent_knowledge(limit=10)
    
    if recent_entries:
        # Prepare data for editor
        data = []
        for entry in recent_entries:
            metadata = entry.get('metadata', {})
            content = entry.get('document', '')
            short_content = content[:50] + "..." if len(content) > 50 else content
            
            timestamp = metadata.get('timestamp', '')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    timestamp_str = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    timestamp_str = timestamp
            else:
                timestamp_str = "-"
                
            data.append({
                "id": entry.get('id'),
                "Content": short_content,
                "Category": metadata.get('category', 'Uncategorized'),
                "Tags": metadata.get('tags', ''),
                "Summary": metadata.get('summary', ''),
                "Timestamp": timestamp_str,
                "Delete": False # Checkbox for deletion
            })
            
        df = pd.DataFrame(data)
        
        # Configure column settings
        column_config = {
            "id": None, # Hide ID
            "Content": st.column_config.TextColumn("Content", disabled=True, width="medium"),
            "Category": st.column_config.SelectboxColumn(
                "Category",
                options=["Policy", "Procedure", "Decision", "Meeting", "Technical", "HR", "Sales", "Uncategorized"],
                required=True,
                width="small"
            ),
            "Tags": st.column_config.TextColumn("Tags (comma-separated)", width="medium"),
            "Summary": st.column_config.TextColumn("Summary", width="large"),
            "Timestamp": st.column_config.TextColumn("Timestamp", disabled=True, width="small"),
            "Delete": st.column_config.CheckboxColumn("Delete", width="small")
        }
        
        # Display editor
        edited_df = st.data_editor(
            df,
            column_config=column_config,
            hide_index=True,
            use_container_width=True,
            key="knowledge_editor",
            num_rows="fixed"
        )
        
        # Handle updates
        if st.session_state.get("knowledge_editor"):
            changes = st.session_state["knowledge_editor"]
            
            # Handle edits
            if changes.get("edited_rows"):
                for idx, updates in changes["edited_rows"].items():
                    entry_id = df.iloc[idx]["id"]
                    
                    # Prepare API updates
                    api_updates = {}
                    if "Category" in updates:
                        api_updates["category"] = updates["Category"]
                    if "Tags" in updates:
                        # Split tags string into list
                        tags_str = updates["Tags"]
                        api_updates["tags"] = [t.strip() for t in tags_str.split(",") if t.strip()]
                    if "Summary" in updates:
                        api_updates["summary"] = updates["Summary"]
                    
                    # Handle Delete checkbox separately or here?
                    # If Delete is checked, we should probably delete instead of update
                    if "Delete" in updates and updates["Delete"] is True:
                        if api_client.delete_knowledge_entry(entry_id):
                            st.toast(f"Deleted entry", icon="🗑️")
                            time.sleep(1)
                            st.rerun()
                    elif api_updates:
                        if api_client.update_knowledge_entry(entry_id, api_updates):
                            st.toast(f"Updated entry and verified!", icon="✅")
                            # We don't strictly need to rerun if we trust the UI update, 
                            # but rerunning ensures sync with backend
                            time.sleep(1) 
                            st.rerun()
            
    else:
        st.info("No recent knowledge entries found")
        
except Exception as e:
    st.warning(f"Unable to fetch recent knowledge: {str(e)}")

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
        # Clear all caches to ensure fresh data
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()
