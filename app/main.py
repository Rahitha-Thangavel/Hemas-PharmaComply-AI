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
from utils.sidebar_clean import render_sidebar
from services.history_manager import HistoryManager

def run_chat_interface():
    # Always create a fresh chat for each new app session, but keep autosaving
    # the active conversation so abrupt closes do not lose the current thread.
    if 'history_manager' not in st.session_state:
        st.session_state.history_manager = HistoryManager()

    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = None
        st.session_state.initialized = False
        st.session_state.messages = []

    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = st.session_state.history_manager.create_new_session()
        st.session_state.messages = []

    render_sidebar()

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

        # Custom CSS for Sources
        st.markdown("""
        <style>
        .source-card {
            background-color: white;
            border-left: 5px solid #003366;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .source-header {
            font-weight: 700;
            color: #003366;
            margin-bottom: 5px;
            display: flex;
            align-items: center;
        }
        .source-meta {
            font-size: 0.85rem;
            color: #64748b;
            margin-bottom: 10px;
        }
        .source-excerpt {
            font-size: 0.95rem;
            color: #334155;
            line-height: 1.5;
            font-style: italic;
            border-left: 2px solid #e2e8f0;
            padding-left: 10px;
        }
        </style>
        """, unsafe_allow_html=True)

        # Display previous messages
        import base64
        
        for i, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                if "sources" in message and message["sources"]:
                    st.markdown("### 📚 Verified Sources")
                    
                    for idx, source in enumerate(message["sources"]):
                        doc_name = source['document']
                        page_num = source['page']
                        file_path = source.get('file_path', '')
                        excerpt = source['excerpt']
                        
                        # Source Card
                        with st.container():
                            st.markdown(f"""
                            <div class="source-card">
                                <div class="source-header">📄 {doc_name}</div>
                                <div class="source-meta">📍 Page {page_num}</div>
                                <div class="source-excerpt">"{excerpt}"</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            col1, col2 = st.columns([0.3, 0.7])
                            
                            # Copy Citation
                            citation_text = f"Source: {doc_name}, Page {page_num}"
                            if col1.button(f"📋 Copy Citation", key=f"copy_{i}_{idx}"):
                                st.toast("Citation copied to clipboard!")
                                components.html(f"""
                                <script>
                                navigator.clipboard.writeText("{citation_text}");
                                </script>
                                """, height=0)

                            # Optimized PDF Viewer: Show only the cited page as an image to support large files
                            if file_path and os.path.exists(file_path):
                                if col2.button(f"🔍 View Document (Page {page_num})", key=f"view_{i}_{idx}"):
                                    with st.expander("📄 Document Viewer", expanded=True):
                                        try:
                                            import pypdfium2
                                            pdf = pypdfium2.PdfDocument(file_path)
                                            
                                            # Convert page_num to 0-indexed for pypdfium2
                                            try:
                                                p_idx = int(page_num) - 1 if str(page_num).isdigit() else 0
                                                if p_idx < 0: p_idx = 0
                                                if p_idx >= len(pdf): p_idx = len(pdf) - 1
                                                
                                                page = pdf[p_idx]
                                                bitmap = page.render(scale=2)  # High-quality rendering
                                                pil_image = bitmap.to_pil()
                                                
                                                # Show page as image
                                                st.image(pil_image, caption=f"Page {page_num} of {doc_name}", use_container_width=True)
                                                
                                                # Add download button for the original file
                                                with open(file_path, "rb") as f:
                                                    st.download_button(
                                                        label="📥 Download Full PDF",
                                                        data=f,
                                                        file_name=doc_name,
                                                        mime="application/pdf",
                                                        key=f"dl_{i}_{idx}"
                                                    )
                                            except Exception as page_e:
                                                st.error(f"Could not render page {page_num}: {page_e}")
                                            finally:
                                                pdf.close()
                                        except Exception as e:
                                            st.error(f"Could not load PDF: {e}")
            
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
