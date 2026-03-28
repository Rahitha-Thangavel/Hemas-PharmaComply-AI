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
        page_title="Impact Predictor - Hemas PharmaComply AI",
        page_icon="📊",
        layout="wide"
    )
    
    # Render synchronized sidebar
    render_sidebar()
    
    st.title("📊 Impact Predictor")
    st.markdown("---")
    
    st.info("💡 **Coming Soon:** This analysis engine will help you predict the financial and operational impact of new NMRA gazette announcements on Hemas products. You will receive customized reports for specific product categories.")
    
    # Placeholder UI
    st.subheader("Hemas Product Categories under review")
    st.write("Section under development...")

if __name__ == "__main__":
    main()
