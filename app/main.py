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
# from app.features.compliance.compliance_service import ComplianceService


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
        if os.path.exists("assets/logo.png"):
            st.image("assets/logo.png", width=60)
        elif os.path.exists("../assets/logo.png"):
            st.image("../assets/logo.png", width=60)
    with col2:
        st.title("Hemas PharmaComply AI")
    
    st.divider()

    # Routing
    run_chat_interface(chatbot)

if __name__ == "__main__":
    main()
