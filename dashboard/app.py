import json
import sys
from pathlib import Path

# Add project root directory to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st

from analysis.reliability import ReliabilityAnalyzer
from storage.database import get_db_connection, init_db

# Page Configuration
st.set_page_config(
    page_title="LLM Agent Reliability Analyzer",
    page_icon="🤖",
    layout="wide"
)

# Initialize Database
init_db()
analyzer = ReliabilityAnalyzer()

st.title("🤖 LLM Agent Trace & Reliability Analyzer")
st.caption("Observability and failure analysis system for tool-using AI agents")

st.divider()

# Instantiate Tabs
tab_overview, tab_tools, tab_traces = st.tabs([
    "📊 System Overview", 
    "🛠️ Tool Analytics", 
    "🔍 Interactive Trace Viewer"
])

# -------------------------------------------------------------------
# TAB 1: SYSTEM OVERVIEW
# -------------------------------------------------------------------
with tab_overview:
    metrics = analyzer.compute_overall_metrics()
    accuracy_data = analyzer.compute_tool_selection_accuracy()
    
    # KPI Metrics Row
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Agent Runs", metrics["total_runs"])
    col2.metric("Success Rate", f"{metrics['success_rate']}%")
    col3.metric("Tool Selection Accuracy", f"{accuracy_data['accuracy']}%")
    col4.metric("Avg Latency", f"{metrics['avg_latency_ms']} ms")
    col5.metric("Avg Steps / Run", metrics["avg_steps"])
    
    st.divider()
    
    # Visualizations Row: Failure Taxonomy & Status Breakdown
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("Failure Taxonomy Breakdown")
        taxonomy = analyzer.compute_failure_taxonomy()
        if taxonomy:
            df_tax = pd.DataFrame(list(taxonomy.items()), columns=["Failure Type", "Count"])
            fig_tax = px.bar(
                df_tax, 
                x="Failure Type", 
                y="Count", 
                color="Failure Type",
                text="Count",
                title="Primary Cause of Failure"
            )
            st.plotly_chart(fig_tax, use_container_width=True)
        else:
            st.info("No failure records detected in current execution traces.")

    with col_chart2:
        st.subheader("Run Success vs Failure Ratio")
        if metrics["total_runs"] > 0:
            df_pie = pd.DataFrame({
                "Status": ["Success", "Failed"],
                "Count": [metrics["successful_runs"], metrics["failed_runs"]]
            })
            fig_pie = px.pie(
                df_pie, 
                names="Status", 
                values="Count", 
                color="Status",
                color_discrete_map={"Success": "#2ecc71", "Failed": "#e74c3c"},
                hole=0.4
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No run data available.")

# -------------------------------------------------------------------
# TAB 2: TOOL ANALYTICS
# -------------------------------------------------------------------
with tab_tools:
    st.subheader("Tool Execution & Latency Statistics")
    tool_stats = analyzer.compute_tool_metrics()
    
    if tool_stats:
        df_tools = pd.DataFrame.from_dict(tool_stats, orient="index").reset_index()
        df_tools.rename(columns={"index": "Tool Name"}, inplace=True)
        
        st.dataframe(df_tools, use_container_width=True)
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            fig_calls = px.bar(
                df_tools, 
                x="Tool Name", 
                y="total_calls", 
                title="Total Calls per Tool",
                color="Tool Name"
            )
            st.plotly_chart(fig_calls, use_container_width=True)
            
        with col_t2:
            fig_lat = px.bar(
                df_tools, 
                x="Tool Name", 
                y="avg_latency_ms", 
                title="Average Execution Latency (ms)",
                color="Tool Name"
            )
            st.plotly_chart(fig_lat, use_container_width=True)
    else:
        st.info("No tool execution traces logged yet.")

# -------------------------------------------------------------------
# TAB 3: INTERACTIVE TRACE VIEWER
# -------------------------------------------------------------------
with tab_traces:
    st.subheader("Execution Trace Inspector")
    
    # Query all run IDs
    with get_db_connection() as conn:
        runs_df = pd.read_sql_query("SELECT run_id, user_prompt, status, success FROM agent_runs ORDER BY start_time DESC;", conn)
        
    if not runs_df.empty:
        run_options = {
            f"{row['run_id']} | Prompt: '{row['user_prompt'][:40]}...' | [{row['status']}]": row['run_id'] 
            for _, row in runs_df.iterrows()
        }
        
        selected_label = st.selectbox("Select Agent Run ID to Inspect:", options=list(run_options.keys()))
        selected_run_id = run_options[selected_label]
        
        # Load specific run details and trace events
        with get_db_connection() as conn:
            run_details = pd.read_sql_query("SELECT * FROM agent_runs WHERE run_id = ?;", conn, params=(selected_run_id,)).iloc[0]
            events_df = pd.read_sql_query("SELECT * FROM trace_events WHERE run_id = ? ORDER BY step_number ASC;", conn, params=(selected_run_id,))
            
        # Display Run Header Meta
        st.markdown(f"### Run Inspection: `{selected_run_id}`")
        meta_col1, meta_col2, meta_col3, meta_col4 = st.columns(4)
        meta_col1.write(f"**User Prompt:** {run_details['user_prompt']}")
        meta_col2.write(f"**Overall Status:** `{run_details['status']}`")
        meta_col3.write(f"**Total Steps:** {run_details['total_steps']}")
        meta_col4.write(f"**Total Latency:** {run_details['total_latency_ms']:.2f} ms")
        
        st.divider()
        st.markdown("#### Chronological Step Execution Log")
        
        for _, event in events_df.iterrows():
            step_num = event['step_number']
            event_type = event['event_type']
            status = event['status']
            
            with st.expander(f"Step {step_num}: {event_type} - [{status}]", expanded=True):
                e_col1, e_col2 = st.columns(2)
                with e_col1:
                    st.write(f"**Tool Name:** `{event['tool_name'] or 'N/A'}`")
                    st.write(f"**Error Type:** `{event['error_type']}`")
                    st.write(f"**Retry Count:** `{event['retry_count']}`")
                    st.write(f"**Latency:** `{event['latency_ms']:.2f} ms`")
                with e_col2:
                    if event['tool_input']:
                        st.caption("Tool Input:")
                        st.code(event['tool_input'], language="json")
                    if event['tool_output']:
                        st.caption("Tool Output / Observation:")
                        st.code(event['tool_output'], language="text")
                    if event['error_message']:
                        st.error(f"Error Message: {event['error_message']}")
    else:
        st.info("No runs found in database. Execute queries via Agent or scripts/run_experiment.py to generate traces.")