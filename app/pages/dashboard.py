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
        page_title="Deadline Tracker - Hemas PharmaComply AI",
        page_icon="⏰",
        layout="wide"
    )
    
    # Render synchronized sidebar
    render_sidebar()
    
    st.title("⏰ Deadline Tracker")
    st.markdown("---")
    
    st.info("📊 **Coming Soon:** This dashboard will provide an overview of all regulatory implementation deadlines extracted from NMRA gazettes. You will receive automated alerts based on your proximity to these critical dates.")
    
    # Placeholder UI
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Upcoming Deadlines", "0")
    with col2:
        st.metric("Critical Actions", "0")
    with col3:
        st.metric("System Health", "✅")
    
    st.subheader("Upcoming Regulatory Dates")
    st.write("Section under development...")

if __name__ == "__main__":
    main()
