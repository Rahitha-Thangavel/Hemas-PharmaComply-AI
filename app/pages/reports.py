import streamlit as st
import os
import sys

# Add root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.sidebar_clean import render_sidebar

def main():
    st.set_page_config(
        page_title="Change Detector - Hemas PharmaComply AI",
        page_icon="🔄",
        layout="wide"
    )
    
    # Render synchronized sidebar
    render_sidebar()
    
    st.title("🔄 Change Detector")
    st.markdown("---")
    
    st.info("💡 **Coming Soon:** This automated monitor will track the publication of new NMRA gazettes and alert you to changes in pricing, registration, or labeling requirements immediately.")
    
    # Placeholder UI
    st.subheader("Recent Regulatory Updates")
    st.write("Section under development...")

if __name__ == "__main__":
    main()
