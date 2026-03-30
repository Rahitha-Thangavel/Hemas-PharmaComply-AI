import os
import sys
from pathlib import Path
import yaml
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

# Add the project root to the python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.core.config_loader import load_config
from app.core.chatbot import HemasPharmaComplyAI
from utils.sidebar_clean import render_sidebar
from services.history_manager import HistoryManager

# Feature Services
from app.features.compliance.compliance_service import ComplianceService

def run_chat_interface(chatbot):
    st.markdown("## 💬 Compliance Assistant (QA)")
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    def handle_query(prompt_text):
        st.session_state.messages.append({"role": "user", "content": prompt_text})
        with st.chat_message("user"):
            st.markdown(prompt_text)
        
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            try:
                message_placeholder.markdown("Thinking...")
                generator = chatbot.stream_query(prompt_text)
                final_data = None
                
                for item in generator:
                    if isinstance(item, str):
                        full_response += item
                        message_placeholder.markdown(full_response + "▌")
                    elif isinstance(item, dict):
                        if "error" in item:
                            message_placeholder.error(item["error"])
                            return
                        elif "type" in item and item["type"] == "final":
                            final_data = item
                            message_placeholder.markdown(item["answer"])
                
                if final_data:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": final_data["answer"],
                        "sources": final_data.get("sources", []),
                        "suggestions": final_data.get("suggestions", [])
                    })
                    st.session_state.history_manager.save_session(
                        st.session_state.current_session_id,
                        st.session_state.messages
                    )
                    st.rerun()
            except Exception as e:
                st.error(f"Query failed: {str(e)}")

    # Display previous messages
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message and message["sources"]:
                st.markdown("### 📚 Sources")
                for source in message["sources"]:
                    with st.expander(f"📚 Source: {source['document']} (Page {source['page']})"):
                        st.markdown(f"**Excerpt:**\n{source['excerpt']}")
        
        if i == len(st.session_state.messages) - 1 and message["role"] == "assistant":
            if "suggestions" in message and message["suggestions"]:
                st.markdown("---")
                st.markdown("### 💡 Suggested Follow-up Questions:")
                cols = st.columns(len(message["suggestions"]))
                for idx, suggestion in enumerate(message["suggestions"]):
                    if cols[idx].button(suggestion, key=f"sugg_{i}_{idx}"):
                        handle_query(suggestion)
    
    if prompt := st.chat_input("Ask about gazette documents..."):
        handle_query(prompt)

def run_risk_detection(chatbot):
    st.markdown("## 🛡️ Risk Detection Module")
    
    compliance_service = ComplianceService(chatbot)
    
    tab1, tab2 = st.tabs(["📝 Assess New Action", "📜 Audit Trail"])
    
    with tab1:
        st.markdown("### 1. Proposed Action Input")
        st.info("Step 2: Accept user input regarding proposed actions (e.g., 'import insulin').")
        
        with st.form("risk_assessment_form"):
            col1, col2 = st.columns(2)
            with col1:
                category = st.selectbox("Action Category:", ["Import Regulation", "Price Adjustment", "Product Registration", "Licensing", "Other"])
                urgency = st.selectbox("Urgency:", ["Low", "Normal", "High", "Critical"])
            with col2:
                product_name = st.text_input("Product Name (Optional):", placeholder="e.g., Insulin")
                action_type = st.selectbox("Action Type:", ["New Import", "Ceiling Price Update", "Renewal", "Variation"])
                
            action_desc = st.text_area("Describe the proposed action in detail:", 
                                     placeholder="e.g., We plan to import 10,000 units of Insulin from Manufacturer X at a proposed MRP of Rs. 650.00.",
                                     height=150)
            
            submitted = st.form_submit_button("Run Risk Detection", type="primary")
            
        if submitted:
            if not action_desc:
                st.warning("Please provide a description of the proposed action.")
            else:
                with st.spinner("Step 3 & 4: Comparing action with regulations and scoring risk..."):
                    result = compliance_service.assess_risk(action_desc, category)
                    
                    if "error" in result:
                        st.error(f"Assessment failed: {result['error']}")
                    else:
                        st.divider()
                        # Step 5: Feedback and Alerts
                        score = result["risk_score"]
                        if score == "High":
                            st.error(f"### 🚩 RISK SCORE: {score}")
                            st.toast("⚠️ High risk detected. Compliance Officers notified via email.", icon="📧")
                        elif score == "Medium":
                            st.warning(f"### ⚠️ RISK SCORE: {score}")
                        else:
                            st.success(f"### ✅ RISK SCORE: {score}")
                        
                        st.markdown(result["assessment"])
                        
                        if "sources" in result and result["sources"]:
                            st.markdown("#### 📚 Document Citations (Step 6)")
                            for src in result["sources"]:
                                st.caption(f"Cited: {src['document']} (Page {src['page']})")
    
    with tab2:
        st.markdown("### 6. Audit Trail")
        st.info("Log of all actions and their associated risk evaluations for audit purposes.")
        
        logs = compliance_service.get_audit_logs()
        if not logs:
            st.info("No audit logs found.")
        else:
            df = pd.DataFrame(logs, columns=["ID", "Timestamp", "Action", "Category", "Score", "Rationale", "Citations", "Actions"])
            st.dataframe(df[["Timestamp", "Category", "Action", "Score"]], use_container_width=True)
            
            selected_id = st.selectbox("View Detailed Log (ID):", [log[0] for log in logs])
            selected_log = next(log for log in logs if log[0] == selected_id)
            
            with st.expander(f"Details for Log ID: {selected_id}", expanded=True):
                st.markdown(f"**Timestamp:** {selected_log[1]}")
                st.markdown(f"**Action:** {selected_log[2]}")
                st.markdown(f"**Risk Score:** {selected_log[4]}")
                st.markdown("**Assessment & Rationale:**")
                st.write(selected_log[5])
                st.markdown("**Citations:**")
                st.code(selected_log[6])

def main():
    st.set_page_config(
        page_title="Hemas PharmaComply AI",
        page_icon="💊",
        layout="wide"
    )

    if 'history_manager' not in st.session_state:
        st.session_state.history_manager = HistoryManager()

    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = st.session_state.history_manager.create_new_session()

    # Sidebar Navigation
    logo_path = os.path.join(project_root, "assets", "logo.png")
    if os.path.exists(logo_path):
        st.sidebar.image(logo_path, width=100)
    st.sidebar.title("Hemas PharmaComply AI")
    st.sidebar.subheader("Compliance Officer Hub")
    
    nav_option = st.sidebar.radio(
        "Navigation",
        ["💬 Chat Assistant", "🛡️ Risk Detection Engine"]
    )
    
    st.sidebar.divider()
    render_sidebar() 

    # Initialize Chatbot
    if 'chatbot' not in st.session_state:
        with st.spinner("Initializing system..."):
            try:
                config = load_config()
                st.session_state.chatbot = HemasPharmaComplyAI(config)
            except Exception as e:
                st.error(f"Initialization failed: {str(e)}")
                return

    chatbot = st.session_state.chatbot

    # Header
    col1, col2 = st.columns([0.1, 0.9])
    with col1:
        if os.path.exists(logo_path):
            st.image(logo_path, width=60)
    with col2:
        st.title("Hemas PharmaComply AI")
    
    st.divider()

    # Routing
    if nav_option == "💬 Chat Assistant":
        run_chat_interface(chatbot)
    elif nav_option == "🛡️ Risk Detection Engine":
        run_risk_detection(chatbot)

if __name__ == "__main__":
    main()
