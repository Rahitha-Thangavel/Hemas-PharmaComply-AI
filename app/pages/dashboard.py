import streamlit as st
import os
import sys
import pandas as pd
from datetime import datetime

# Add root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
# app/pages/dashboard.py -> app/pages -> app -> project_root
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.sidebar_clean import render_sidebar
from app.features.deadline.deadline_service import (
    sync_deadlines, 
    load_deadlines, 
    get_status, 
    send_email_reminders,
    validate_db
)

def main():
    st.set_page_config(
        page_title="Deadline Tracking & Alerts",
        page_icon="⏰",
        layout="wide"
    )
    
    # Render synchronized sidebar
    render_sidebar()
    
    # Premium Header (Logo, Title, Subtitle)
    col1, col2 = st.columns([0.1, 0.9])
    with col1:
        if os.path.exists("assets/logo.png"):
            st.image("assets/logo.png", width=70)
        elif os.path.exists("../assets/logo.png"):
            st.image("../assets/logo.png", width=70)
    with col2:
        st.title("Deadline Tracking & Alerts")
    
    st.markdown("⚡ **Powered by Hemas Compliance Engine**")
    st.divider()
    
    # Tabs for UI
    tab1, tab2 = st.tabs(["Dashboard Overview", "Check for New Deadlines"])
    
    with tab1:
        # Automatic cleanup and load
        data_raw = os.path.join(project_root, "data", "raw")
        validate_db(data_raw)
        deadlines = load_deadlines()
        
        # Filtering UI
        col_f1, col_f2 = st.columns([0.3, 0.7])
        with col_f1:
            filter_option = st.selectbox(
                "🔍 Filter Deadlines",
                ["All Deadlines", "Upcoming", "Urgent", "Finished"],
                key="filter_deadlines"
            )
        
        if not deadlines:
            st.info("No deadlines found. Please upload PDFs or click 'Sync Deadlines'.")
        else:
            # Process data for display
            display_data = []
            metrics = {"Green": 0, "Yellow": 0, "Red": 0, "Grey": 0}
            
            for index, d in enumerate(deadlines):
                # We need to make sure 'action' key exists since json might be old, but we just created it.
                action_text = d.get("action", "Review compliance requirements.")
                color, days_rem = get_status(d["date"])
                
                metrics[color] = metrics.get(color, 0) + 1
                
                # Assign visual indicators
                if color == "Red":
                    status_badge = "🚨 URGENT (≤2 days)"
                    category = "Urgent"
                elif color == "Yellow":
                    status_badge = "⚠️ UPCOMING (3-10 days)"
                    category = "Upcoming"
                elif color == "Green":
                    status_badge = "✅ SAFE (>10 days)"
                    category = "Upcoming"
                elif color == "Grey":
                    status_badge = "⌛ COMPLETED / PAST"
                    category = "Finished"
                else:
                    status_badge = "❓ Unknown"
                    category = "Other"
                
                # Apply Filter
                if filter_option == "Upcoming" and category != "Upcoming":
                    continue
                if filter_option == "Urgent" and category != "Urgent":
                    continue
                if filter_option == "Finished" and category != "Finished":
                    continue
                
                display_data.append({
                    "Document": d["source"],
                    "Deadline": d["date"],
                    "Days Remaining": days_rem,
                    "Status": status_badge,
                    "Action Required": action_text
                })
                
            if not display_data:
                st.info(f"No deadlines found matching the filter: **{filter_option}**")
            else:
                # Quick Stats
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Urgent", metrics.get("Red", 0))
                with col2:
                    st.metric("Upcoming", metrics.get("Yellow", 0) + metrics.get("Green", 0))
                with col3:
                    st.metric("Safe", metrics.get("Green", 0))
                with col4:
                    st.metric("Finished", metrics.get("Grey", 0))
                    
                # Render Table
                df = pd.DataFrame(display_data)
                df = df.sort_values(by="Days Remaining", ascending=True)
                
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )
            
            # Action Buttons
            st.markdown("---")
            st.subheader("Actions")
            if st.button("📧 Send Email Reminders", type="primary"):
                sent = send_email_reminders()
                if sent:
                    for s in sent:
                        st.success(s)
                else:
                    st.info("No emails needed to be sent today (no deadlines exactly 7 or 1 day away).")
    
    with tab2:
        st.subheader("PDF Ingestion & Sync")
        st.write("Upload new NMRA gazettes to extract implementation and license deadlines.")
        
        uploaded_files = st.file_uploader("Upload PDF Gazette", type=["pdf"], accept_multiple_files=True)
        if uploaded_files:
            if st.button("Save & Extract"):
                data_dir = os.path.join(project_root, "data", "raw")
                os.makedirs(data_dir, exist_ok=True)
                for uf in uploaded_files:
                    path = os.path.join(data_dir, uf.name)
                    with open(path, "wb") as f:
                        f.write(uf.getbuffer())
                st.success(f"Saved {len(uploaded_files)} file(s) to 'data/raw'.")
                
                # Check for new
                with st.spinner("Extracting deadlines... (using regex/logic)"):
                    new_count = sync_deadlines(data_dir)
                    st.success(f"Extraction complete! Found {new_count} new deadline(s).")
                    st.rerun() # Lively update overview
                    
        st.markdown("---")
        st.write("Or scan the existing data folder for new files:")
        if st.button("🔄 Sync Existing 'data/raw' Directory"):
            data_dir = os.path.join(project_root, "data", "raw")
            if os.path.exists(data_dir):
                with st.spinner("Scanning and extracting from 'data/raw'..."):
                    new_count = sync_deadlines(data_dir)
                    st.success(f"Sync complete! Found {new_count} new deadline(s).")
                    st.rerun() # Lively update overview
            else:
                st.error("The 'data/raw' directory not found. Please upload files.")

if __name__ == "__main__":
    main()
