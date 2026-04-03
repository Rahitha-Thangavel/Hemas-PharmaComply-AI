import streamlit as st
import os
import sys
import tempfile
import base64
import mimetypes
import shutil
import pandas as pd
from pathlib import Path

# Add root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.sidebar_clean import render_sidebar
import services.change_detector as cd_module
import importlib
importlib.reload(cd_module)
from services.file_loader import load_documents
from services.categorizer import analyze_document, rename_and_update_metadata, sync_all_documents
from services.regulation_audit_service import RegulationAuditService
import streamlit.components.v1 as components

def open_file_in_new_tab(file_path):
    """Uses a JavaScript-based Blob object approach to open files in a new tab."""
    if not file_path:
        return
    
    try:
        file_name = os.path.basename(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"
            
        with open(file_path, "rb") as f:
            base64_data = base64.b64encode(f.read()).decode("utf-8")
            
        html_code = f'''
        <button id="open-document-btn" style="
            display: inline-block;
            padding: 0.5em 1.2em;
            color: #FFFFFF;
            background-color: #003366;
            border-radius: 5px;
            text-decoration: none;
            font-weight: bold;
            border: 1px solid #003366;
            cursor: pointer;
            width: 100%;
            font-family: sans-serif;
            text-align: center;
        ">👁️ Open Final Document ({file_name})</button>

        <script>
            document.getElementById('open-document-btn').onclick = function() {{
                try {{
                    const base64Data = "{base64_data}";
                    const byteCharacters = atob(base64Data);
                    const byteNumbers = new Array(byteCharacters.length);
                    for (let i = 0; i < byteCharacters.length; i++) {{
                        byteNumbers[i] = byteCharacters.charCodeAt(i);
                    }}
                    const byteArray = new Uint8Array(byteNumbers);
                    const blob = new Blob([byteArray], {{type: "{mime_type}"}});
                    const url = URL.createObjectURL(blob);
                    const newWindow = window.open(url, '_blank');
                }} catch (e) {{
                    console.error("Error opening document:", e);
                }}
            }};
        </script>
        '''
        components.html(html_code, height=50)
    except Exception as e:
        st.error(f"❌ Could not prepare document for viewing: {e}")

def save_uploaded_file(uploaded_file):
    """Save uploaded file to a local project directory."""
    try:
        upload_dir = os.path.join(project_root, "data", "temp_uploads")
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    except Exception as e:
        st.error(f"❌ Failed to save uploaded file: {e}")
        return None

def main():
    st.set_page_config(
        page_title="Smart Regulation Change Detector - Hemas PharmaComply AI",
        page_icon="🔄",
        layout="wide"
    )
    
    # --- UX REFINEMENT: Badge Clearing (Independent) ---
    if st.session_state.get("unread_sync_cd"):
        st.session_state.unread_sync_cd = False
        # Move records from module-specific sync list to page-local state
        sync_results_cd = st.session_state.get("sync_new_files_cd", [])
        if sync_results_cd:
            if "current_page_updates" not in st.session_state:
                st.session_state.current_page_updates = []
            st.session_state.current_page_updates.extend(sync_results_cd)
            st.session_state.sync_new_files_cd = [] # Clear the specific list
            st.toast("✅ Change Detector badge cleared. Updates ready below.")

    render_sidebar()
    
    audit_service = RegulationAuditService()
    
    st.title("🔄 Smart Regulation Change Detector")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["🔄 Run Comparison", "📜 Audit History"])
    
    with tab1:
        # 1. PRIMARY ACTION: NMRA LIVE SYNC
        st.info("🚀 **NEW: Fully Automated Change Detection.** "
                "Click the **'Check NMRA for Updates'** button below to pull the latest gazettes and compare them instantly.")
        
        col_sync1, col_sync2, col_sync3 = st.columns([1, 2, 1])
        with col_sync2:
            if st.button("🔄 Check NMRA for New Updates", key="page_sync_btn", type="primary", use_container_width=True):
                from utils.sidebar_clean import run_nmra_sync
                run_nmra_sync()
        
        st.markdown("---")
        
        # 2. AUTOMATED UPDATES SECTION (Synced Results)
        page_updates = st.session_state.get("current_page_updates", [])
        if page_updates:
            with st.container():
                st.markdown(
                    """
                    <div style="background-color: #FFF5F5; border-left: 5px solid #EF4444; padding: 1.2rem; border-radius: 10px; margin-bottom: 1.5rem;">
                        <h3 style="color: #003366; margin-top: 0;">🔔 Live Regulatory Updates Ready</h3>
                        <p style="color: #334155;">The following documents were downloaded from NMRA. AI has identified their category and found a previous version for comparison.</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                for i, result in enumerate(page_updates):
                    with st.expander(f"🆕 NEW: {result['category']} - {result['original_name']}", expanded=True):
                        col_a, col_b = st.columns([0.7, 0.3])
                        with col_a:
                            st.write(f"**Identified Year:** {result['year'] if result['year'] else 'Unknown'}")
                            prev_match, _ = cd_module.find_comparison_pair(result["final_path"])
                            if prev_match:
                                st.write(f"**AI Comparison Match Found:** `{os.path.basename(prev_match)}`")
                            else:
                                st.write("**AI Comparison Match Found:** No previous version found. Try manual selection below.")
                                
                        with col_b:
                            if st.button("⚡ Quick Detect Changes", key=f"btn_quick_{i}", type="primary", use_container_width=True):
                                st.session_state.active_new_path = result["final_path"]
                                st.session_state.active_prev_path = prev_match
                                st.session_state.active_category = result["category"]
                                st.session_state.trigger_compare = True
                                # Clean up this update from the list after triggering
                                st.session_state.current_page_updates.pop(i)
                                st.rerun()
                
                if st.button("🗑️ Dismiss All Sync Notifications", use_container_width=True):
                    st.session_state.current_page_updates = []
                    st.rerun()
            st.markdown("---")

        # 3. MANUAL / BACKUP SECTION (Inside Expander)
        with st.expander("🛠️ Manual Selection / Backup Mode", expanded=not page_updates):
            st.write("Use this if you want to compare specific historical files or manually upload a gazette.")
            
            mode = st.radio("Choose Comparison Mode:", 
                            ["Auto-select Previous Document (Recommended)", "Manual Upload (Upload Both Files)"],
                            horizontal=True)
            
            categories = ["Price Control", "Registration & Fees", "Labelling & Requirements", "Other Regulations"]
            selected_category = st.selectbox("Document Category:", categories)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Previous Gazette")
                if "Auto-select" in mode:
                    matches = cd_module.list_all_documents_in_category(selected_category)
                    if matches:
                        display_options = {m["path"]: f"{m['year'] if m['year'] else 'Unknown'} - {m['original_name']}" for m in matches}
                        selected_path = st.selectbox(f"Select version for **{selected_category}**:", options=list(display_options.keys()), format_func=lambda x: display_options[x])
                        st.session_state.active_prev_path = selected_path
                        open_file_in_new_tab(selected_path)
                    else:
                        st.warning("No documents found for this category.")
                else:
                    prev_file = st.file_uploader("Upload previous gazette file", type=['pdf', 'docx', 'txt', 'png', 'jpg', 'jpeg'], key="prev_gazette")
                    if prev_file:
                        st.session_state.active_prev_path = save_uploaded_file(prev_file)
            
            with col2:
                st.subheader("New Gazette")
                new_file_up = st.file_uploader("Upload new gazette file", type=['pdf', 'docx', 'txt', 'png', 'jpg', 'jpeg'], key="new_gazette")
                if new_file_up:
                    st.session_state.active_new_path = save_uploaded_file(new_file_up)
                    open_file_in_new_tab(st.session_state.active_new_path)
            
            if st.button("🚀 Run Manual Detection", use_container_width=True):
                st.session_state.active_category = selected_category
                st.session_state.trigger_compare = True
                st.rerun()

        # 4. RESULTS DISPLAY & AUTO-SAVE
        if st.session_state.get("trigger_compare"):
            prev_path = st.session_state.get('active_prev_path')
            new_path = st.session_state.get('active_new_path')
            category = st.session_state.get('active_category', "Regulation")
            
            if not prev_path or not new_path:
                st.error("❌ Both files must be selected for comparison.")
                st.session_state.trigger_compare = False
            else:
                try:
                    summary = cd_module.compare_gazettes(prev_path, new_path)
                    
                    # --- AUTO-SAVE LOGIC ---
                    audit_service.log_change(category, prev_path, new_path, summary)
                    st.toast("💾 Change summary automatically saved to Audit History!", icon="🛡️")

                    st.markdown("---")
                    st.header(f"📝 Summary of Changes: {category}")
                    st.markdown(summary)
                    
                    st.download_button(label="📥 Download Summary", data=summary, file_name="change_summary.txt", mime="text/plain")
                    
                    st.markdown("---")
                    st.subheader("💡 What's next?")
                    if st.button("📊 Run Hemas Impact Analysis on this File", type="primary", use_container_width=True):
                        st.session_state.redirect_to_impact = True
                        st.session_state.impact_target_path = new_path
                        st.session_state.impact_prev_path = prev_path
                        st.session_state.impact_category = category
                        st.switch_page("pages/impact_analysis.py")
                except Exception as e:
                    st.error(f"Failed to process: {e}")
                finally:
                    st.session_state.trigger_compare = False

    with tab2:
        st.markdown("### 📜 Change Audit Trail")
        st.info("Log of all historical regulation comparisons and their AI summaries.")
        
        logs = audit_service.get_logs()
        if not logs:
            st.info("No audit logs found.")
        else:
            # logs = (id, timestamp, category, prev_file, new_file, summary)
            df = pd.DataFrame(logs, columns=["ID", "Timestamp", "Category", "Previous File", "New File", "Summary"])
            st.dataframe(df[["Timestamp", "Category", "Previous File", "New File"]], use_container_width=True)
            
            selected_id = st.selectbox("Select Audit to View Detail (ID):", [log[0] for log in logs])
            selected_log = next(log for log in logs if log[0] == selected_id)
            
            with st.container():
                st.markdown(f"**Timestamp:** `{selected_log[1]}`")
                st.markdown(f"**Files:** `{selected_log[3]}` ➔ `{selected_log[4]}`")
                st.divider()
                st.markdown("### AI Summary Result")
                st.markdown(selected_log[5])
                
                if st.button(f"📥 Download Summary #{selected_id}", key=f"dl_{selected_id}"):
                    st.download_button(label="Click to confirm download", data=selected_log[5], file_name=f"audit_{selected_id}.txt")

    st.caption("Developed by Hemas PharmaComply AI Core Team | 2025")

if __name__ == "__main__":
    main()
