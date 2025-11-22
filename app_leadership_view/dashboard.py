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
    page_title="Knowledge-Weaver Dashboard",
    page_icon="🕷️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Dark Theme & Robot Accessibility ---
st.markdown("""
    <style>
    /* Global Dark Theme Adjustments */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    </style>
""", unsafe_allow_html=True)

# --- Header ---
st.title("🕷️ Knowledge-Weaver Dashboard")
st.markdown("*Leadership View: Verify knowledge, bridge gaps, and manage the Source of Truth.*")

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
# Metrics functions

# Metrics functions
# Metrics functions
def render_metrics():
    """Render dashboard metrics using real data"""
    try:
        metrics = api_client.fetch_dashboard_metrics()
        
        if not metrics:
            st.error("Failed to load metrics")
            return

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Total Knowledge",
                value=metrics.get("total_knowledge", 0),
                help="Total number of entries in the knowledge base"
            )

        with col2:
            st.metric(
                label="Verified Ratio",
                value=f"{metrics.get('verified_ratio', 0)}%",
                help="Percentage of entries verified by humans"
            )

        with col3:
            st.metric(
                label="Query Volume (7d)",
                value=metrics.get("query_volume_7d", 0),
                help="Total queries in the last 7 days"
            )

        with col4:
            st.metric(
                label="Knowledge Gaps",
                value=metrics.get("knowledge_gaps_7d", 0),
                help="Queries with 0 results in the last 7 days"
            )
            
        # Knowledge Gaps Table
        recent_gaps = metrics.get("recent_gaps", [])
        if recent_gaps:
            st.markdown("### 🚨 Knowledge Gaps (Needs Attention)")
            st.caption("Top unanswered queries from the team")
            
            gap_data = []
            gap_options = ["Select a gap to answer..."]
            
            for gap in recent_gaps:
                query = gap.get('query', '')
                count = gap.get('count', 0)
                timestamp = gap.get('last_asked', '')
                
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    timestamp_str = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    timestamp_str = timestamp
                    
                gap_data.append({
                    "Query": query,
                    "Frequency": count,
                    "Last Asked": timestamp_str
                })
                gap_options.append(f"{query} ({count} attempts)")
            
            col_table, col_action = st.columns([2, 1])
            
            with col_table:
                st.dataframe(
                    pd.DataFrame(gap_data),
                    column_config={
                        "Query": st.column_config.TextColumn("Missing Topic", width="large"),
                        "Frequency": st.column_config.NumberColumn("Attempts", width="small"),
                        "Last Asked": st.column_config.TextColumn("Last Attempt", width="medium")
                    },
                    hide_index=True,
                    use_container_width=True
                )
            
            with col_action:
                st.markdown("#### Bridge the Gap")
                
                # Initialize session state for gap selection
                if 'selected_gap_index' not in st.session_state:
                    st.session_state.selected_gap_index = 0
                
                selected_gap_str = st.selectbox(
                    "Select a gap to answer:", 
                    options=gap_options,
                    index=st.session_state.selected_gap_index,
                    key="gap_selector"
                )
                
                if selected_gap_str != "Select a gap to answer...":
                    # Extract query from selection string
                    selected_query = selected_gap_str.rsplit(" (", 1)[0]
                    
                    def submit_gap_answer():
                        answer_content = st.session_state.gap_answer_input
                        answer_category = st.session_state.gap_category_selector
                        
                        if answer_content:
                            try:
                                if api_client.ingest_knowledge(
                                    text=answer_content,
                                    url="dashboard-manual-entry",
                                    category=answer_category,
                                    tags=["#KnowledgeGapFilled"],
                                    summary=selected_query
                                ):
                                    st.session_state.selected_gap_index = 0
                                    st.session_state.gap_answer_input = "" # Explicitly clear input
                                    st.toast("Answer submitted and verified! 🚀", icon="✅")
                                else:
                                    st.toast("Failed to submit answer.", icon="❌")
                            except Exception as e:
                                st.error(f"Backend Offline or Error: {e}")

                    with st.form(key="answer_gap_form", clear_on_submit=False):
                        st.caption(f"Answering: **{selected_query}**")
                        
                        # Initialize answer input in session state if not present
                        if "gap_answer_input" not in st.session_state:
                            st.session_state.gap_answer_input = ""
                            
                        st.text_area(
                            "Answer Content", 
                            height=150, 
                            placeholder="Type the verified answer here...",
                            key="gap_answer_input"
                        )
                        st.selectbox("Category", ["Policy", "Procedure", "Technical", "HR", "Sales", "Other"], key="gap_category_selector")
                        
                        # Use callback to handle submission and clearing BEFORE rerun
                        st.form_submit_button("Submit Answer", type="primary", on_click=submit_gap_answer)
            
    except Exception as e:
        st.error(f"Error rendering metrics: {e}")

# Render metrics
render_metrics()



# Tabbed Interface for Active Items and Recycle Bin
st.markdown("---")

# Robot-friendly markers
st.markdown('<span data-testid="knowledge-tabs-section"></span>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📚 Active Items", "🗑️ Recycle Bin"])

with tab1:
    st.markdown('<span data-testid="active-items-tab"></span>', unsafe_allow_html=True)
    st.subheader("Recent Knowledge Ingestions")
    
    try:
        recent_entries = api_client.fetch_recent_knowledge(limit=10, deleted_only=False)
        
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
            st.markdown('<span data-testid="knowledge-editor-container"></span>', unsafe_allow_html=True)
            edited_df = st.data_editor(
                df,
                column_config=column_config,
                hide_index=True,
                use_container_width=True,
                key="knowledge_editor",
                num_rows="fixed"
            )
            
            # Check for delete requests first (before handling edits)
            # Use the original df to get IDs since the id column is hidden in edited_df
            rows_to_delete = []
            for idx, row in edited_df.iterrows():
                if row.get("Delete", False):
                    # Look up the ID from the original df using the index
                    entry_id = df.iloc[idx]["id"]
                    content = row["Content"]
                    
                    # Debug logging
                    print(f"[DELETE REQUEST] Index: {idx}, ID: {entry_id}, Content: {content}")
                    
                    rows_to_delete.append({
                        "idx": idx,
                        "id": entry_id,
                        "content": content
                    })
            
            # If there are items to delete, show confirmation
            if rows_to_delete:
                st.warning(f"⚠️ You have marked {len(rows_to_delete)} item(s) for deletion.")
                
                with st.expander("🗑️ Confirm Deletion", expanded=True):
                    st.markdown('<span data-testid="delete-confirmation-dialog"></span>', unsafe_allow_html=True)
                    st.markdown("**Items to be deleted:**")
                    for item in rows_to_delete:
                        st.markdown(f"- {item['content']}")
                    
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        if st.button("✅ Confirm Delete", type="primary", use_container_width=True, key="confirm_delete_btn"):
                            deleted_count = 0
                            for item in rows_to_delete:
                                print(f"[DELETE API CALL] Attempting to delete ID: {item['id']}")
                                if api_client.delete_knowledge_entry(item["id"]):
                                    print(f"[DELETE SUCCESS] Deleted ID: {item['id']}")
                                    deleted_count += 1
                                else:
                                    print(f"[DELETE FAILED] Failed to delete ID: {item['id']}")
                            
                            if deleted_count > 0:
                                st.success(f"Deleted {deleted_count} item(s)!")
                                time.sleep(1.5)
                                st.rerun()
                            else:
                                st.error("Failed to delete items.")
                    with col2:
                        if st.button("❌ Cancel", use_container_width=True, key="cancel_delete_btn"):
                            st.rerun()
            
            # Handle edits (only process if no deletes pending)
            elif st.session_state.get("knowledge_editor"):
                changes = st.session_state["knowledge_editor"]
                
                # Handle edits
                if changes.get("edited_rows"):
                    for idx, updates in changes["edited_rows"].items():
                        entry_id = df.iloc[idx]["id"]
                        
                        # Prepare API updates (skip Delete field)
                        api_updates = {}
                        if "Category" in updates:
                            api_updates["category"] = updates["Category"]
                        if "Tags" in updates:
                            # Split tags string into list
                            tags_str = updates["Tags"]
                            api_updates["tags"] = [t.strip() for t in tags_str.split(",") if t.strip()]
                        if "Summary" in updates:
                            api_updates["summary"] = updates["Summary"]
                        
                        if api_updates:
                            if api_client.update_knowledge_entry(entry_id, api_updates):
                                st.toast(f"Updated entry and verified!", icon="✅")
                                time.sleep(1) 
                                st.rerun()
                
        else:
            st.info("No active knowledge entries found")
            
    except Exception as e:
        st.warning(f"Unable to fetch recent knowledge: {str(e)}")

with tab2:
    st.markdown('<span data-testid="recycle-bin-tab"></span>', unsafe_allow_html=True)
    st.subheader("Recycle Bin")
    st.caption("Soft-deleted items can be restored here")
    
    try:
        deleted_entries = api_client.fetch_recent_knowledge(limit=20, deleted_only=True)
        
        if deleted_entries:
            # Prepare data for table
            recycle_data = []
            for entry in deleted_entries:
                metadata = entry.get('metadata', {})
                content = entry.get('document', '')
                short_content = content[:50] + "..." if len(content) > 50 else content
                
                deleted_at = metadata.get('deleted_at', '')
                if deleted_at:
                    try:
                        dt = datetime.fromisoformat(deleted_at.replace('Z', '+00:00'))
                        deleted_str = dt.strftime('%Y-%m-%d %H:%M')
                    except:
                        deleted_str = deleted_at
                else:
                    deleted_str = "-"
                    
                recycle_data.append({
                    "id": entry.get('id'),
                    "Content": short_content,
                    "Category": metadata.get('category', 'Uncategorized'),
                    "Tags": metadata.get('tags', ''),
                    "Summary": metadata.get('summary', ''),
                    "Deleted At": deleted_str
                })
            
            recycle_df = pd.DataFrame(recycle_data)
            
            # Display table
            st.markdown('<span data-testid="recycle-bin-table"></span>', unsafe_allow_html=True)
            st.dataframe(
                recycle_df[["Content", "Category", "Tags", "Summary", "Deleted At"]],
                hide_index=True,
                use_container_width=True
            )
            
            # Restore functionality
            st.markdown("### Restore Item")
            st.markdown('<span data-testid="restore-section"></span>', unsafe_allow_html=True)
            selected_idx = st.selectbox(
                "Select item to restore:",
                options=range(len(recycle_data)),
                format_func=lambda i: f"{recycle_data[i]['Content']} (Deleted: {recycle_data[i]['Deleted At']})",
                key="restore_selector"
            )
            
            if st.button("🔄 Restore Selected Item", type="primary", key="restore-btn"):
                entry_id = recycle_data[selected_idx]["id"]
                if api_client.restore_knowledge_entry(entry_id):
                    st.success(f"Item restored successfully!")
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error("Failed to restore item.")
        else:
            st.info("Recycle bin is empty")
            
    except Exception as e:
        st.warning(f"Unable to fetch deleted items: {str(e)}")

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
    
    if st.button("Refresh Dashboard", key="refresh_dashboard_btn"):
        # Clear all caches to ensure fresh data
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()
