import streamlit as st
import yaml
from pathlib import Path
from services.history_manager import HistoryManager

def render_sidebar():
    # Inject Custom CSS for Premium Design (Sidebar and Global overrides)
    st.markdown("""
        <style>
        /* Smooth transitions and fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        * {
            font-family: 'Inter', sans-serif;
        }
        
        /* Glassmorphism for main content */
        .stApp {
            background-color: #F8FAFC;
        }
        
        /* ------------------------ SIDEBAR STYLING ------------------------ */
        /* Make the sidebar deep blue */
        [data-testid="stSidebar"] {
            background-color: #001f3f !important; /* Deep deep blue to match dashboard */
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* Target all text inside sidebar to be white/lightgray */
        [data-testid="stSidebar"] * {
            color: #E2E8F0 !important;
        }
        
        /* Adjust spacing for the custom content */
        [data-testid="stSidebarUserContent"] {
            padding-top: 1rem !important;
            padding-bottom: 2rem !important;
        }
        
        /* Hide native streamlit navigation so we can inject our own nicely ordered ones */
        [data-testid="stSidebarNav"] {
            display: none !important;
        }
        
        /* Style the custom page links to look like premium dashboard tabs */
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
        
        /* Highlight active page */
        a[data-testid="stPageLink"][aria-current="page"] {
            background-color: rgba(255,255,255, 0.15) !important;
            border-left: 4px solid #3b82f6 !important;
            font-weight: 600;
        }
        
        /* Remove the weird background from the active nav SVG */
        a[data-testid="stPageLink"][aria-current="page"] svg {
            fill: #3b82f6 !important;
        }
        
        /* ------------------------ MAIN STYLING ------------------------ */
        /* Stylish buttons with micro-animations */
        div.stButton > button {
            background: linear-gradient(135deg, #003366 0%, #004d99 100%);
            color: white !important;
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px -1px rgba(0, 51, 102, 0.2);
            font-weight: 500;
        }
        div.stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 51, 102, 0.3);
            border: none;
        }
        
        /* Floating Chat Input */
        .stChatFloatingInputContainer {
            background: rgba(255, 255, 255, 0.8) !important;
            backdrop-filter: blur(12px) !important;
            border-top: 1px solid rgba(0, 51, 102, 0.1);
            padding-bottom: 2rem !important;
        }
        
        /* Chat bubbles styling */
        .stChatMessage {
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }
        
        /* Header styling */
        h1 {
            color: #003366 !important;
            font-weight: 700 !important;
            letter-spacing: -0.5px;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.image("assets/logo.png", width='stretch')
        st.markdown("---")
        
        # 1. System Status Logic
        try:
            with open("config/config.yaml", "r") as f:
                config = yaml.safe_load(f)
            provider = config.get('llm_provider', 'groq').upper()
            model = config.get(provider.lower(), {}).get('model', 'Unknown')
        except:
            provider, model = "Unknown", "Unknown"
            
        data_dir = Path("./data")
        file_count = 0
        if data_dir.exists():
            files = list(data_dir.rglob("*.pdf")) + list(data_dir.rglob("*.txt")) + list(data_dir.rglob("*.docx"))
            file_count = len(files)

        st.markdown("##### 📊 SYSTEM STATUS")
        st.markdown(f"● **System:** Online\n\n📁 **Gazettes:** {file_count} documents loaded\n\n🧠 **LLM:** {provider} | {model}")
        
        st.markdown("---")
        
        # 2. Main Navigation
        # Determine paths relative to where the script is run
        # If in a subpage, the path to main.py is '../main.py'
        # But st.page_link handles these relatively correctly if given from the entry point context.
        # Actually, st.page_link needs relative path from the entrypoint file ONLY if in multi-page mode.
        # Since 'main.py' is the entrypoint in 'app/', and pages are in 'app/pages/', 
        # the paths should be relative to 'app/'.
        
        st.markdown("##### 🎯 MAIN NAVIGATION")
        st.page_link("main.py", label="Q&A Assistant", icon="💬", help="Ask questions about NMRA regulations")
        st.page_link("pages/dashboard.py", label="Deadline Tracker", icon="⏰", help="Track implementation deadlines")
        st.page_link("pages/compliance_checker.py", label="Risk Evaluator", icon="⚠️", help="Check compliance of proposed actions")
        st.page_link("pages/impact_analysis.py", label="Impact Predictor", icon="📊", help="Analyze regulation impact on Hemas products")
        st.page_link("pages/reports.py", label="Change Detector", icon="🔄", help="Monitor new gazette publications")
        
        st.markdown("---")
        
        # 3. Chat History
        st.markdown("##### 🕒 CHAT HISTORY")
        
        # Initialize history manager and session if not in state
        if 'history_manager' not in st.session_state:
            st.session_state.history_manager = HistoryManager()
            
        if 'current_session_id' not in st.session_state:
            sessions = st.session_state.history_manager.get_all_sessions()
            if sessions:
                st.session_state.current_session_id = sessions[0]['id']
                st.session_state.messages = st.session_state.history_manager.get_session(sessions[0]['id']).get('messages', [])
            else:
                new_id = st.session_state.history_manager.create_new_session()
                st.session_state.current_session_id = new_id
                st.session_state.messages = []
            
        if st.button("➕ New Chat", width='stretch'):
            new_id = st.session_state.history_manager.create_new_session()
            st.session_state.current_session_id = new_id
            st.session_state.messages = []
            st.rerun()
            
        sessions = st.session_state.history_manager.get_all_sessions()
        for session in sessions:
            title = session['title']
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                # Use st.session_state.get() to avoid KeyErrors
                curr_id = st.session_state.get('current_session_id')
                if session['id'] == curr_id:
                   # Workaround: disable current chat button
                   st.button(f"📂 {title}", key=f"btn_{session['id']}", disabled=True, width='stretch')
                else:
                    if st.button(f"📄 {title}", key=f"btn_{session['id']}", width='stretch'):
                        st.session_state.current_session_id = session['id']
                        st.session_state.messages = st.session_state.history_manager.get_session(session['id']).get('messages', [])
                        st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{session['id']}", help="Delete this chat"):
                    st.session_state.history_manager.delete_session(session['id'])
                    if session['id'] == st.session_state.get('current_session_id'):
                        updated_sessions = st.session_state.history_manager.get_all_sessions()
                        if updated_sessions:
                            next_session = updated_sessions[0]
                            st.session_state.current_session_id = next_session['id']
                            st.session_state.messages = st.session_state.history_manager.get_session(next_session['id']).get('messages', [])
                        else:
                            new_id = st.session_state.history_manager.create_new_session()
                            st.session_state.current_session_id = new_id
                            st.session_state.messages = []
                    st.rerun()
                    
        st.markdown("---")
        
        # 4. Configuration
        st.markdown("##### ⚙️ CONFIGURATION")
        with st.expander("🔧 Settings", expanded=False):
            st.markdown("• **LLM Configuration:** " + provider)
            st.markdown("• **Email Alerts:** Enabled")
            st.markdown("• **Data Sources:** Local Directory")
            
        st.markdown("---")
        
        # 5. Alerts
        st.markdown("##### 🔔 ALERTS")
        with st.expander("⚠️ System Alerts", expanded=False):
            st.markdown("📧 **Email notifications:** ✅ Enabled")
            st.markdown("⏳ **Last alert:** 7 days before deadline")
            st.button("⚙️ Configure Alerts", key="cfg_alerts_sidebar")
            
        st.markdown("---")
        
        # 6. Version
        st.markdown("##### ℹ️ VERSION")
        st.caption("v1.0.0 | Hemas Holdings | 2025")
