import streamlit as st
import os
import sys
import pandas as pd
from datetime import datetime
from pathlib import Path

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
from app.core.config_loader import load_config
from app.core.chatbot import HemasPharmaComplyAI

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
    
    # Initialize Chatbot for AI Analysis if needed
    if 'chatbot' not in st.session_state:
        with st.spinner("Initializing compliance engine..."):
            try:
                config = load_config()
                st.session_state.chatbot = HemasPharmaComplyAI(config)
            except Exception as e:
                st.error(f"Chatbot init failed: {e}")

    # Tabs for UI
    tab1, tab2 = st.tabs(["Dashboard Overview", "Check for New Deadlines"])
    
    with tab1:
        # Automatic cleanup and load
        data_raw_dir = os.path.join(project_root, "data", "raw")
        validate_db(data_raw_dir)
        deadlines = load_deadlines()
        
        # Filtering UI
        col_f1, col_f2 = st.columns([0.3, 0.7])
        with col_f1:
            filter_option = st.selectbox(
                "🔍 Filter Deadlines",
                ["Upcoming", "Urgent", "Finished", "All Deadlines"],
                index=0,
                key="filter_deadlines"
            )
        
        if not deadlines:
            st.info("No deadlines found. Please upload PDFs or click 'Sync Deadlines'.")
        else:
            # Process data for display
            display_list = []
            metrics = {"Green": 0, "Yellow": 0, "Red": 0, "Grey": 0, "Completed": 0}
            
            for index, d in enumerate(deadlines):
                status = d.get("status", "Pending")
                action_text = d.get("action", "Review compliance requirements.")
                color, days_rem = get_status(d["date"])
                
                # Assign visual indicators
                if status != "Pending":
                    status_badge = f"🛡️ {status.upper()}"
                    category = "Finished"
                    metrics["Completed"] += 1
                else:
                    metrics[color] = metrics.get(color, 0) + 1
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
                        status_badge = "⌛ OVERDUE"
                        category = "Urgent"
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
                
                display_list.append({
                    "ID": d["id"],
                    "Document": d["source"],
                    "Deadline": d["date"],
                    "Days Remaining": days_rem,
                    "Status": status_badge,
                    "Action Required": action_text,
                    "Context": d.get("context", "No context saved."),
                    "RawStatus": status
                })
            if not display_list:
                st.info(f"No deadlines found matching the filter: **{filter_option}**")
            else:
                # Quick Stats
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                with col_m1:
                    st.metric("Urgent", metrics.get("Red", 0) + (1 if metrics.get("Grey", 0) > 0 and filter_option != "Finished" else 0))
                with col_m2:
                    st.metric("Upcoming", metrics.get("Yellow", 0) + metrics.get("Green", 0))
                with col_m3:
                    st.metric("Completed", metrics["Completed"])
                with col_m4:
                    st.metric("Total Tracked", len(deadlines))
                    
                # Render Table with Actions
                st.markdown("### Compliance Deadlines")
                
                for i, item in enumerate(display_list):
                    with st.expander(f"{item['Status']} | {item['Document']} ({item['Deadline']})", expanded=(item['RawStatus'] == "Pending")):
                        col_a, col_b = st.columns([0.65, 0.35])
                        
                        with col_a:
                            st.markdown(f"**📍 Action Required:** {item['Action Required']}")
                            if item['RawStatus'] == 'Pending':
                                st.write(f"⏳ **Time Remaining:** {item['Days Remaining']} days")
                            else:
                                st.write(f"✅ **Completion Status:** {item['RawStatus']}")
                            
                            st.markdown(f"**🔍 Source Context:**")
                            st.info(f'"{item["Context"]}"')
                            
                        with col_b:
                            # 1. VIEW DOCUMENT
                            file_path = os.path.join(data_raw_dir, item["Document"])
                            if os.path.exists(file_path):
                                if st.button(f"👁️ View Document", key=f"view_{item['ID']}"):
                                    st.session_state.view_pdf = file_path
                                    st.session_state.view_doc_name = item["Document"]
                                    st.toast("Opening high-quality preview below...")
                            
                            # 2. AI ANALYSIS
                            if st.button(f"📝 Analyze Requirement (AI)", key=f"ai_{item['ID']}"):
                                with st.spinner("AI is reading the document section..."):
                                    prompt = f"Explain the practical compliance requirements for a Hemas products officer for the following deadline mentioned in {item['Document']}: '{item['Context']}' which is due on {item['Deadline']}. What specific actions are needed for Hemas?"
                                    response = st.session_state.chatbot.direct_query(prompt)
                                    st.markdown("---")
                                    st.markdown("**🤖 AI Compliance Insight:**")
                                    st.success(response)

                        # MARK AS SUBMITTED SECTION
                        st.markdown("---")
                        c1, c2, c3 = st.columns([0.4, 0.3, 0.3])
                        if item['RawStatus'] == "Pending":
                            with c2:
                                if st.button("Mark Submitted", key=f"sub_{item['ID']}"):
                                    from app.features.deadline.deadline_service import update_deadline_status
                                    update_deadline_status(item['ID'], "Submitted")
                                    st.success("Marked as Submitted!")
                                    st.rerun()
                            with c3:
                                if st.button("Mark Renewed", key=f"ren_{item['ID']}"):
                                    from app.features.deadline.deadline_service import update_deadline_status
                                    update_deadline_status(item['ID'], "Renewed")
                                    st.success("Marked as Renewed!")
                                    st.rerun()
                        else:
                            with c2:
                                if st.button("Revert to Pending", key=f"rev_{item['ID']}"):
                                    from app.features.deadline.deadline_service import update_deadline_status
                                    update_deadline_status(item['ID'], "Pending")
                                    st.rerun()
                
                # --- GLOBAL PDF VIEWER (Renders here if triggered) ---
                if "view_pdf" in st.session_state and st.session_state.view_pdf:
                    st.divider()
                    st.markdown(f"## 📄 Original Gazette Viewer: {st.session_state.view_doc_name}")
                    if st.button("❌ Close Viewer"):
                        st.session_state.view_pdf = None
                        st.rerun()
                    
                    try:
                        import pypdfium2
                        pdf = pypdfium2.PdfDocument(st.session_state.view_pdf)
                        
                        # Show first 2 pages for reference, or a selector?
                        # Let's show a range slider for pages
                        num_pages = len(pdf)
                        
                        # Only show slider if there's more than 1 page
                        if num_pages > 1:
                            page_range = st.select_slider("Select page to view:", options=range(1, num_pages + 1), value=1)
                        else:
                            page_range = 1
                            st.info("Single-page document.")
                        
                        p_idx = page_range - 1
                        page = pdf[p_idx]
                        bitmap = page.render(scale=3) # Ultra-sharp
                        pil_image = bitmap.to_pil()
                        st.image(pil_image, caption=f"Page {page_range} of {num_pages}", use_container_width=True)
                        
                        # Download Button
                        with open(st.session_state.view_pdf, "rb") as f:
                            st.download_button("📥 Download Full PDF", f, file_name=st.session_state.view_doc_name, mime="application/pdf")
                            
                        pdf.close()
                    except Exception as e:
                        st.error(f"Could not load PDF in premium viewer: {e}")

            # Global Action Buttons
            st.markdown("---")
            st.subheader("Global Actions")
            if st.button("📧 Trigger Manual Alert Check", type="primary", help="Checks all pending deadlines for 7-day and 1-day milestones."):
                sent = send_email_reminders()
                if sent:
                    for s in sent:
                        st.success(s)
                else:
                    st.info("No new alerts to send. Either no deadlines are at milestones, or alerts were already sent.")
    
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
