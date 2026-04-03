import streamlit as st
import yaml
import os
import datetime
import json
from pathlib import Path
from services.history_manager import HistoryManager
from services.nmra_watcher import NMRAWatcher
from app.core.config_loader import load_config
from services.categorizer import analyze_document, rename_and_update_metadata


@st.dialog("🗑️ Clear All History")
def confirm_clear_all_history():
    st.markdown("### Are you sure?")
    st.write("This will permanently delete ALL your previous conversations. This action cannot be undone.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes, Clear All", type="primary", use_container_width=True):
            st.session_state.history_manager.clear_all_history()
            st.session_state.current_session_id = st.session_state.history_manager.create_new_session()
            st.session_state.messages = []
            st.toast("History cleared!")
            st.rerun()
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()


@st.dialog("🗑️ Delete Chat")
def confirm_delete_session(session_id, title):
    st.markdown(f"### Delete this chat?")
    st.write(f"Are you sure you want to delete: **'{title}'**?")
    
    is_curr = session_id == st.session_state.get("current_session_id")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes, Delete", type="primary", use_container_width=True):
            st.session_state.history_manager.delete_session(session_id)
            if is_curr:
                st.session_state.current_session_id = st.session_state.history_manager.create_new_session()
                st.session_state.messages = []
            st.toast("Chat deleted!")
            st.rerun()
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()


def run_nmra_sync():
    """
    Triggers the NMRA Watcher sync and handles notifications.
    """
    import os  # Fail-safe local import
    config = load_config()
    watcher = NMRAWatcher(config)
    
    with st.spinner("🔄 Syncing with NMRA website..."):
        results = watcher.sync()
        
    if results["new_files"]:
        st.toast(f"✅ Successfully downloaded {results['downloaded']} new gazette(s)!")
        
        sync_results = []
        for file in results["new_files"]:
            file_path = os.path.join(config["paths"]["data_dir"], file)
            with st.status(f"🔍 Analyzing {file}...") as status:
                category, year = analyze_document(file_path)
                final_path = rename_and_update_metadata(file_path, category, year)
                
                sync_results.append({
                    "original_name": file,
                    "final_path": final_path,
                    "category": category,
                    "year": year
                })
                status.update(label=f"✅ Categorized as {category} ({year})", state="complete")
        
        # --- NEW: Independent Results for CD and Impact ---
        if "sync_new_files_cd" not in st.session_state:
            st.session_state.sync_new_files_cd = []
        if "sync_new_files_impact" not in st.session_state:
            st.session_state.sync_new_files_impact = []
        
        st.session_state.sync_new_files_cd.extend(sync_results)
        st.session_state.sync_new_files_impact.extend(sync_results)
        
        # Set unread flags
        st.session_state.unread_sync_cd = True
        st.session_state.unread_sync_impact = True
        
        # Trigger chatbot (auto-loading documents)
        if 'chatbot' in st.session_state:
            st.info("🔄 Ingesting new documents into AI database...")
            st.session_state.chatbot.auto_load_gazettes()
            st.toast("✅ Documents ingested! AI is now updated.")
    elif results["errors"]:
        st.error(f"❌ Sync failed: {results['errors'][0]}")
    else:
        st.session_state.sync_message = "✅ NMRA documents are up to date. (Live Scan Verified)"
        st.toast("ℹ️ System is up to date.")
        
    st.session_state.last_sync = datetime.datetime.now().strftime("%I:%M:%S %p")
    st.rerun()


def render_sidebar():
    # Inject Custom CSS for Premium Design
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        * {
            font-family: 'Inter', sans-serif;
        }

        .stApp {
            background-color: #F8FAFC;
        }

        [data-testid="stSidebar"] {
            background-color: #001f3f !important;
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }

        [data-testid="stSidebar"] * {
            color: #E2E8F0 !important;
        }

        [data-testid="stSidebarUserContent"] {
            padding-top: 1rem !important;
            padding-bottom: 2rem !important;
        }

        [data-testid="stSidebarNav"] {
            display: none !important;
        }

        a[data-testid="stPageLink"] {
            border-radius: 8px;
            margin: 4px 16px;
            padding: 8px 16px;
            transition: all 0.3s ease;
            text-decoration: none !important;
            display: flex;
            align-items: center;
        }

        a[data-testid="stPageLink"]:hover {
            background-color: rgba(255,255,255, 0.1) !important;
            transform: translateX(4px);
        }

        a[data-testid="stPageLink"][aria-current="page"] {
            background-color: rgba(255,255,255, 0.15) !important;
            border-left: 4px solid #3b82f6 !important;
            font-weight: 600;
        }

        a[data-testid="stPageLink"][aria-current="page"] svg {
            fill: #3b82f6 !important;
        }

        div.stButton > button {
            background: linear-gradient(135deg, #003366 0%, #004d99 100%);
            color: white !important;
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px -1px rgba(0, 51, 102, 0.2);
            font-weight: 500;
            width: 100%;
        }

        div.stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 51, 102, 0.3);
            border: none;
        }

        .stChatFloatingInputContainer {
            background: rgba(255, 255, 255, 0.8) !important;
            backdrop-filter: blur(12px) !important;
            border-top: 1px solid rgba(0, 51, 102, 0.1);
            padding-bottom: 2rem !important;
        }

        /* 
           Main Titles (Deep Blue for Visibility on White BG)
        */
        h1, h2, h3, h4, h5 {
            color: #003366 !important;
            font-weight: 700 !important;
        }
        
        /* 
           Sidebar Labels (Light Gray for Visibility on Deep Blue BG)
        */
        [data-testid="stSidebar"] h1, 
        [data-testid="stSidebar"] h2, 
        [data-testid="stSidebar"] h3, 
        [data-testid="stSidebar"] h4, 
        [data-testid="stSidebar"] h5 {
            color: #E2E8F0 !important;
        }

        .stChatMessage {
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }
        .clear-btn [data-testid="stBaseButton-secondary"]:hover {
            background-color: #3b82f6 !important;
            color: white !important;
            border: none !important;
        }

        
        /* Individual Delete Button */
        .del-btn [data-testid="stBaseButton-secondary"] {
            background-color: transparent !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            padding: 0 !important;
            min-width: 35px !important;
        }
        .del-btn [data-testid="stBaseButton-secondary"]:hover {
            background-color: rgba(239, 68, 68, 0.2) !important;
            border-color: #ef4444 !important;
        }

        
        .chat-row {
            display: flex;
            align-items: center;
            gap: 5px;
            width: 100%;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        # 1. HEMAS LOGO
        try:
            st.image("assets/logo.png", use_container_width=True)
        except Exception:
            try:
                st.image("assets/logo.png", use_container_width=True)
            except:
                st.subheader("💊 Hemas PharmaComply")
        
        st.markdown("---")

        # 2. SYSTEM STATUS
        try:
            with open("config/config.yaml", "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            provider = config.get("llm_provider", "groq").upper()
            model = config.get(provider.lower(), {}).get("model", "Unknown")
        except:
            provider, model = "Unknown", "Unknown"

        data_dir = Path("./data")
        file_count = 0
        if data_dir.exists():
            files = list(data_dir.rglob("*.pdf")) + list(data_dir.rglob("*.txt")) + list(data_dir.rglob("*.docx"))
            file_count = len(files)

        st.markdown("##### 📊 SYSTEM STATUS")
        st.markdown(f"**System:** Online\n\n📁 **Gazettes:** {file_count} documents\n\n🧠 **LLM:** {provider}")
        
        # 2.1 SYNC BUTTON
        if st.button("🔄 Sync with NMRA", key="btn_nmra_sync_v6", use_container_width=True, help="Scan the NMRA website for new gazettes"):
            run_nmra_sync()
        
        last_sync = st.session_state.get("last_sync", "Never")
        st.caption(f"Last Live Sync: {last_sync}")
        
        st.markdown("---")

        # 3. CONFIGURATIONS
        st.markdown("##### ⚙️ CONFIGURATIONS")
        with st.expander("Safe Settings", expanded=False):
            st.markdown("- **Model:** " + model)
            st.markdown("- **Email Notifications:** Active")
            st.markdown("- **Theme:** Dash Blue")

        st.markdown("---")

        # 4. MENUS (MAIN NAVIGATION)
        st.markdown("##### 🎯 MENUS")
        st.page_link("main.py", label="Home Dashboard", icon=":material/home:", help="Back to main dashboard")
        st.page_link("pages/1_qa_assistant.py", label="Q&A Assistant", icon=":material/chat:", help="Ask questions about NMRA regulations")
        st.page_link("pages/dashboard.py", label="Deadline Tracker", icon=":material/schedule:", help="Track implementation deadlines")
        st.page_link("pages/compliance_checker.py", label="Risk Evaluator", icon=":material/warning:", help="Check compliance of proposed actions")
        
        # --- FIXED: Only depends on unread_sync_impact ---
        impact_label = "Impact Predictor"
        if st.session_state.get("unread_sync_impact"):
            impact_label += " 🔴"
        st.page_link("pages/impact_analysis.py", label=impact_label, icon=":material/monitoring:", help="Analyze regulation impact on Hemas products")
        
        # --- FIXED: Only depends on unread_sync_cd ---
        cd_label = "Change Detector"
        if st.session_state.get("unread_sync_cd"):
            cd_label += " 🔴"
        st.page_link("pages/reports.py", label=cd_label, icon=":material/autorenew:", help="Detect changes between new and previous price gazettes")

        st.markdown("---")

        # 5. CHAT HISTORY
        st.markdown("##### 🕒 CHAT HISTORY")
        
        if "history_manager" not in st.session_state:
            st.session_state.history_manager = HistoryManager()
        if "show_full_history" not in st.session_state:
            st.session_state.show_full_history = False
            
        # 5.1 New Chat Button
        if st.button("➕ New Chat", key="btn_new_chat_v6", use_container_width=True):
            st.session_state.current_session_id = st.session_state.history_manager.create_new_session()
            st.session_state.messages = []
            st.session_state.show_full_history = False
            st.rerun()

        # Sessions List (Latest 3 + More Toggle)
        try:
            sessions = st.session_state.history_manager.get_all_sessions()
            if not sessions:
                st.caption("No previous conversations.")
            else:
                # 5.2 Clear All Button
                st.markdown('<div class="clear-btn">', unsafe_allow_html=True)
                if st.button("🗑️ Clear All History", key="btn_clear_history_v7", use_container_width=True, help="Permanently delete all conversations"):
                    confirm_clear_all_history()
                st.markdown('</div>', unsafe_allow_html=True)

                show_full = st.session_state.get('show_full_history', False)
                visible_sessions = sessions if show_full else sessions[:3]
                
                for session in visible_sessions:
                    is_curr = session["id"] == st.session_state.get("current_session_id")
                    title = session["title"]
                    label = f"📁 {title}"
                    if is_curr:
                        label = f"👉 {title} (Active)"
                    
                    col_link, col_del = st.columns([0.8, 0.2])
                    
                    with col_link:
                        if st.button(label, key=f"hbtn_v7_{session['id']}", disabled=is_curr, use_container_width=True):
                            st.session_state.current_session_id = session["id"]
                            st.session_state.messages = st.session_state.history_manager.get_session(session["id"]).get("messages", [])
                            st.session_state.show_full_history = False
                            st.rerun()
                    
                    with col_del:
                        st.markdown('<div class="del-btn">', unsafe_allow_html=True)
                        if st.button("🗑️", key=f"del_v7_{session['id']}", help="Delete this chat"):
                            confirm_delete_session(session["id"], session["title"])
                        st.markdown('</div>', unsafe_allow_html=True)

                # More / Less toggle
                if len(sessions) > 3:
                    toggle_label = "🔼 Show Less" if show_full else f"🔽 More ({len(sessions)-3})"
                    if st.button(toggle_label, key="btn_toggle_history_v6", use_container_width=True):
                        st.session_state.show_full_history = not show_full
                        st.rerun()
        except Exception as e:
            st.error(f"History list error: {e}")

        st.markdown("---")

        # 6. OTHER (ALERTS & VERSION)
        st.markdown("##### 📣 ALERTS")
        with st.expander("System Alerts", expanded=False):
            st.markdown("- **Email notifications:** Enabled")
            st.markdown("- **Last alert:** 7 days before deadline")
            st.button("Configure", key="cfg_sidebar_v5")
        
        st.markdown("---")
        st.markdown("##### ℹ️ VERSION")
        st.caption("v1.0.0 | Hemas Holdings | 2026")
