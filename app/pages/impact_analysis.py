import streamlit as st
import os
import sys
import pandas as pd
import shutil
import mimetypes
import base64
import json
from pathlib import Path
from datetime import datetime
import streamlit.components.v1 as components

# Add root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.core.config_loader import load_config
from app.core.chatbot import HemasPharmaComplyAI
from app.features.impact_analysis.impact_service import ImpactService
from services.impact_audit_service import ImpactAuditService
from utils.sidebar_clean import render_sidebar
from services.categorizer import analyze_document, rename_and_update_metadata

def open_file_in_new_tab(file_path):
    """Uses a JavaScript-based Blob object approach to open files in a new tab."""
    if not file_path: return
    try:
        file_name = os.path.basename(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type: mime_type = "application/octet-stream"
        with open(file_path, "rb") as f:
            base64_data = base64.b64encode(f.read()).decode("utf-8")
        html_code = f'''
        <button id="open-doc-btn" style="
            display: inline-block; padding: 0.5em 1.2em; color: #FFFFFF; background-color: #003366;
            border-radius: 5px; text-decoration: none; font-weight: bold; border: 1px solid #003366;
            cursor: pointer; width: 100%; font-family: sans-serif; text-align: center;
        ">👁️ View Document ({file_name})</button>
        <script>
            document.getElementById('open-doc-btn').onclick = function() {{
                const base64Data = "{base64_data}";
                const byteCharacters = atob(base64Data);
                const byteNumbers = new Array(byteCharacters.length);
                for (let i = 0; i < byteCharacters.length; i++) {{ byteNumbers[i] = byteCharacters.charCodeAt(i); }}
                const byteArray = new Uint8Array(byteNumbers);
                const blob = new Blob([byteArray], {{type: "{mime_type}"}});
                const url = URL.createObjectURL(blob);
                window.open(url, '_blank');
            }};
        </script>
        '''
        components.html(html_code, height=50)
    except: pass

def save_to_data_folder(file_path):
    """Copies a file from temp_uploads to the permanent data/raw folder and organizes it."""
    try:
        data_raw_dir = os.path.join(project_root, "data", "raw")
        os.makedirs(data_raw_dir, exist_ok=True)
        file_name = os.path.basename(file_path)
        target_path = os.path.join(data_raw_dir, file_name)
        shutil.copy(file_path, target_path)
        with st.status("🔍 Analyzing and organizing document...") as status:
            category, year = analyze_document(target_path)
            new_path = rename_and_update_metadata(target_path, category, year)
            status.update(label=f"✅ Saved to library as '{category}' ({year})", state="complete")
        return new_path
    except Exception as e:
        st.error(f"❌ Failed to save: {e}"); return None

def save_uploaded_file(uploaded_file):
    """Save uploaded file to a local temp directory."""
    try:
        upload_dir = os.path.join(project_root, "data", "temp_uploads")
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    except Exception as e:
        st.error(f"❌ Upload failed: {e}"); return None

def main():
    st.set_page_config(
        page_title="Impact Predictor - Hemas PharmaComply AI",
        page_icon="📊", layout="wide"
    )
    
    # --- UX REFINEMENT: Badge Dismissal (Independent) ---
    if st.session_state.get("unread_sync_impact"):
        st.session_state.unread_sync_impact = False
        # Move records from module-specific sync list to page-local state
        sync_results_impact = st.session_state.get("sync_new_files_impact", [])
        if sync_results_impact:
            if "current_impact_updates" not in st.session_state:
                st.session_state.current_impact_updates = []
            st.session_state.current_impact_updates.extend(sync_results_impact)
            st.session_state.sync_new_files_impact = [] # Clear the specific list
            st.toast("✅ Impact Predictor badge cleared. Updates ready below.")

    render_sidebar()

    if 'chatbot' not in st.session_state:
        with st.spinner("Initializing system..."):
            try:
                config = load_config()
                st.session_state.chatbot = HemasPharmaComplyAI(config)
            except Exception as e:
                st.error(f"Init failed: {e}"); return

    chatbot = st.session_state.chatbot
    products_csv = os.path.join(project_root, "data", "products.csv")
    impact_service = ImpactService(chatbot, products_csv)
    audit_service = ImpactAuditService()

    st.title("📊 Impact Predictor")
    st.markdown("Analyze how the latest NMRA gazette regulations affect Hemas's specific product catalog.")
    
    # Handle incoming data from Change Detector Redirect
    is_redirected = st.session_state.get('redirect_to_impact', False)
    if 'current_target_path' not in st.session_state:
        st.session_state.current_target_path = None

    if is_redirected:
        st.success("📌 **Redirection Success:** Analyzing the file you just identified in the Change Detector.")
        st.session_state.current_target_path = st.session_state.get('impact_target_path')
        st.session_state.redirect_to_impact = False 

    st.divider()
    
    tab1, tab2 = st.tabs(["📊 Run Impact Analysis", "📜 Impact Audit History"])
    
    with tab1:
        # --- NMRA SYNC BUTTON ---
        st.info("🚀 **NEW: Fully Automated Impact Prediction.** "
                "Check for the latest NMRA updates and see their impact on your business instantly.")
        
        col_sync1, col_sync2, col_sync3 = st.columns([1, 2, 1])
        with col_sync2:
            if st.button("🔄 Check NMRA for New Updates", key="page_sync_btn_impact", type="primary", use_container_width=True):
                from utils.sidebar_clean import run_nmra_sync
                run_nmra_sync()
        
        st.divider()

        # --- LIVE UPDATES CARD ---
        impact_updates = st.session_state.get("current_impact_updates", [])
        if impact_updates:
            with st.container():
                st.markdown(
                    """
                    <div style="background-color: #F0F9FF; border-left: 5px solid #0EA5E9; padding: 1.2rem; border-radius: 10px; margin-bottom: 1.5rem;">
                        <h3 style="color: #003366; margin-top: 0;">🔔 New Regulation Updates Detected</h3>
                        <p style="color: #334155;">The following documents were synced from NMRA. Run an impact analysis to see how these affects your current product portfolio.</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                for i, result in enumerate(impact_updates):
                    with st.expander(f"🆕 NEW: {result['category']} - {result['original_name']}", expanded=True):
                        col_a, col_b = st.columns([0.7, 0.3])
                        with col_a:
                            st.write(f"**Identified Year:** {result['year'] if result['year'] else 'Unknown'}")
                            st.write(f"**Document Link:** `{result['final_path']}`")
                        with col_b:
                            if st.button("⚡ Quick Impact Analysis", key=f"btn_impact_quick_{i}", type="primary", use_container_width=True):
                                st.session_state.current_target_path = result["final_path"]
                                st.session_state.trigger_impact_analysis = True
                                # Remove from list after triggering
                                st.session_state.current_impact_updates.pop(i)
                                st.rerun()
                
                if st.button("🗑️ Dismiss All Impact Notifications", use_container_width=True):
                    st.session_state.current_impact_updates = []
                    st.rerun()
            st.divider()

        # --- MANUAL UPLOAD SECTION ---
        with st.expander("🛠️ Manual Selection / Backup Mode", expanded=False):
            col1, col2 = st.columns([0.6, 0.4])
            active_path = None
            
            with col1:
                st.subheader("📁 Manual Gazette Analysis")
                uploaded_file = st.file_uploader("Select NEW Gazette PDF to Analyze:", type=['pdf'], key="impact_up_final_v2")
                
                if uploaded_file:
                    path = save_uploaded_file(uploaded_file)
                    if path:
                        st.session_state.current_target_path = path
                        st.success(f"📄 **Current Document:** {uploaded_file.name}")
                        m_c1, m_c2 = st.columns(2)
                        with m_c1: open_file_in_new_tab(path)
                        with m_c2:
                            if st.button("📥 Add to Permanent Library", key="btn_save_perm_impact_v2"):
                                saved = save_to_data_folder(path); 
                                if saved: st.session_state.current_target_path = saved; st.balloons()
                elif st.session_state.current_target_path:
                    st.info(f"📄 **Active Document:** {os.path.basename(st.session_state.current_target_path)}")
                    open_file_in_new_tab(st.session_state.current_target_path)
                    
                active_path = st.session_state.current_target_path

            with col2:
                st.subheader("📚 Hemas Catalog Status")
                if os.path.exists(products_csv):
                    df_cat = pd.read_csv(products_csv)
                    st.success(f"Connected: `{len(df_cat)}` Products")
                    with st.expander("Preview Internal Prices"):
                        st.dataframe(df_cat[['product_brand', 'active_ingredient', 'strength', 'current_mrp']].head(10), use_container_width=True)
                else: st.error("products.csv not found!")

        # --- RUN ANALYSIS ---
        st.divider()
        if st.button("🚀 Run Impact Analysis", type="primary", use_container_width=True) or st.session_state.get("trigger_impact_analysis"):
            st.session_state.trigger_impact_analysis = False
            if not active_path:
                st.error("❌ Please upload or select a gazette first.")
            else:
                status_box = st.status("🚀 Processing Strategic Analysis...", expanded=True)
                with status_box:
                    st.write(f"📂 Processing: {os.path.basename(active_path)}")
                    chatbot.process_files([active_path])
                    st.write("🔍 Identifying price changes and matching to Hemas products...")
                    results = impact_service.predict_impact(target_filename=os.path.basename(active_path))
                    
                    # --- AUTO-SAVE ---
                    audit_service.log_impact(os.path.basename(active_path), results)
                    st.toast("💾 Business impact results automatically saved to Audit History!", icon="🛡️")

                    st.session_state.impact_results = results
                    st.session_state.diag_findings = impact_service.last_raw_findings
                    st.session_state.diag_response = impact_service.get_last_raw_llm_response()
                    st.session_state.diag_context = impact_service.get_last_retrieved_context()
                    status_box.update(label="✅ Analysis Complete!", state="complete", expanded=False)

        # --- RENDER RESULTS ---
        if 'impact_results' in st.session_state:
            results = st.session_state.impact_results
            if not results:
                st.warning("No regulatory impacts matched your catalog for this document.")
            else:
                st.markdown("### 📈 Impact Summary")
                s_c1, s_c2, s_c3, s_c4 = st.columns(4)
                affected = [r for r in results if r['impact_type'] != "NO CHANGE"]
                s_c1.metric("Impacted Products", f"{len(affected)}")
                s_c2.metric("Critical Alerts", f"{len([r for r in results if r['impact_type'] == 'PRODUCT REMOVED'])}")
                s_c3.metric("High Priority", f"{len([r for r in results if r['priority'] == 'HIGH'])}")
                s_c4.metric("Market Matches", f"{len(results)}")
                
                st.divider()
                st.markdown("### 📋 Product-Specific Impact Plans")
                for i, result in enumerate(results):
                    p_badge = f":red[{result['priority']}]" if result['priority'] in ["CRITICAL", "HIGH"] else (f":orange[{result['priority']}]" if result['priority'] == "MEDIUM" else f":gray[{result['priority']}]")
                    with st.expander(f"**{result['impact_type']}** | {result['brand']} ({result['ingredient']})", expanded=(result['priority'] in ["CRITICAL", "HIGH"])):
                        ca, cb, cc = st.columns([0.4, 0.3, 0.3])
                        with ca:
                            st.markdown(f"**Generic:** {result['ingredient']}")
                            if result['impact_type'] == "PRODUCT REMOVED": st.write("❌ **REMOVED**")
                            else:
                                delta = ((result['new_price'] - result['old_price']) / result['old_price'] * 100) if result['old_price'] > 0 else 0
                                st.markdown(f"**Pricing:** {result['old_price']:.2f} → **{result['new_price']:.2f}** ({delta:+.1f}%)")
                        with cb: st.markdown(f"**Priority:** {p_badge}"); st.markdown(f"**Effort:** {result['effort']}")
                        with cc: st.markdown(f"📅 **Deadline:** {result['deadline']}")
                        st.markdown("---")
                        st.write("**🏃 Suggested Action Plan:**")
                        for step in result['action_plan']:
                            st.checkbox(step, key=f"step_impact_{i}_{step[:20]}")

                csv_data = pd.DataFrame(results).to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Detailed Impact Report", data=csv_data, file_name=f"Hemas_Impact_Report_{datetime.now().strftime('%Y%m%d')}.csv")

    with tab2:
        st.markdown("### 📜 Business Impact History")
        st.info("Log of all historical business impact analyses conducted by the AI.")
        
        logs = audit_service.get_logs()
        if not logs:
            st.info("No impact audit logs found.")
        else:
            # logs = (id, timestamp, doc_name, affected_count, critical, high, json)
            df = pd.DataFrame(logs, columns=["ID", "Timestamp", "Document", "Affected", "Critical", "High", "Details"])
            st.dataframe(df[["ID", "Timestamp", "Document", "Affected", "Critical", "High"]], use_container_width=True)
            
            selected_id = st.selectbox("View Detailed Report (ID):", [log[0] for log in logs])
            selected_log = next(log for log in logs if log[0] == selected_id)
            
            with st.container():
                st.markdown(f"**Document:** `{selected_log[2]}` | **Timestamp:** `{selected_log[1]}`")
                st.divider()
                st.subheader("Stored Impact Findings")
                hist_results = json.loads(selected_log[6])
                
                for i, r in enumerate(hist_results):
                    st.write(f"**{r['impact_type']}** | {r['brand']} ({r['ingredient']})")
                    st.caption(f"Priority: {r['priority']} | New Price: {r['new_price']} | Deadline: {r['deadline']}")
                    st.markdown("---")

    st.caption("Developed by Hemas PharmaComply AI Core Team | 2026")

if __name__ == "__main__":
    main()
