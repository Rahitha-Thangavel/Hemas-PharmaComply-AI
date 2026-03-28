import os
import sys
from pathlib import Path
import yaml

# Add the project root to the python path so top-level packages can be imported
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
import streamlit.components.v1 as components
from app.core.config_loader import load_config
from app.core.chatbot import HemasPharmaComplyAI
from utils.sidebar import render_sidebar
from services.history_manager import HistoryManager

def run_chat_interface():
    # 0. ALL SESSION STATE INITIALIZATION MUST BE FIRST
    if 'history_manager' not in st.session_state:
        st.session_state.history_manager = HistoryManager()
    
    # Initialize chatbot and flags if not present
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = None
        st.session_state.initialized = False
        st.session_state.messages = []
    
    # Initialize and sync session ID if not present
    if 'current_session_id' not in st.session_state:
        sessions = st.session_state.history_manager.get_all_sessions()
        if sessions:
            st.session_state.current_session_id = sessions[0]['id']
            st.session_state.messages = st.session_state.history_manager.get_session(sessions[0]['id']).get('messages', [])
        else:
            new_id = st.session_state.history_manager.create_new_session()
            st.session_state.current_session_id = new_id
            st.session_state.messages = []

    # 1. Now render the synchronized sidebar
    render_sidebar()

    # 2. Title Section
    col1, col2 = st.columns([0.15, 0.85])
    with col1:
        st.image("assets/logo.png", width=70)
    with col2:
        st.title("Hemas PharmaComply AI")
    st.markdown("⚡ Powered by Groq - Super fast responses")
    
    # Main content
    if not st.session_state.initialized:
        st.info("Initializing Hemas PharmaComply AI...")
        with st.spinner("Loading..."):
            try:
                config = load_config()
                st.session_state.chatbot = HemasPharmaComplyAI(config)
                st.session_state.initialized = True
                st.success("✅ System ready!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Initialization failed: {str(e)}")
    else:
        st.markdown("## 💬 Chat")
        
        def handle_query(prompt_text):
            st.session_state.messages.append({"role": "user", "content": prompt_text})
            with st.chat_message("user"):
                st.markdown(prompt_text)
            
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                try:
                    message_placeholder.markdown("Thinking...")
                    generator = st.session_state.chatbot.stream_query(prompt_text)
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
        layout="wide",
        initial_sidebar_state="expanded"
    )
    run_chat_interface()

if __name__ == "__main__":
    main()
