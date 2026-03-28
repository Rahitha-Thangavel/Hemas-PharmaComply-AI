import streamlit as st
import os
import sys

# Add root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.sidebar import render_sidebar

def main():
    st.set_page_config(
        page_title="Risk Evaluator - Hemas PharmaComply AI",
        page_icon="⚠️",
        layout="wide"
    )
    
    # Render synchronized sidebar
    render_sidebar()
    
    st.title("⚠️ Risk Evaluator")
    st.markdown("---")
    
    st.info("💡 **Coming Soon:** This module will allow you to check the compliance of proposed pharmaceutical actions against NMRA regulations. You will be able to upload drafts or describe actions to receive an immediate risk assessment.")
    
    # Placeholder UI
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Current Compliance Status")
        st.write("Section under development...")
    with col2:
        st.subheader("Risk History")
        st.write("Section under development...")

if __name__ == "__main__":
    main()
