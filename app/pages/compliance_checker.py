import streamlit as st
import os
import sys
import pandas as pd

# Add root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.core.config_loader import load_config
from app.core.chatbot import HemasPharmaComplyAI
from app.features.compliance.compliance_service import ComplianceService
from utils.sidebar_clean import render_sidebar

def main():
    st.set_page_config(
        page_title="Risk Evaluator - Hemas PharmaComply AI",
        page_icon="🛡️",
        layout="wide"
    )
    
    # Render synchronized sidebar
    render_sidebar()

    # Initialize Chatbot if not exists
    if 'chatbot' not in st.session_state:
        with st.spinner("Initializing system..."):
            try:
                config = load_config()
                st.session_state.chatbot = HemasPharmaComplyAI(config)
            except Exception as e:
                st.error(f"Initialization failed: {str(e)}")
                return

    chatbot = st.session_state.chatbot
    compliance_service = ComplianceService(chatbot)

    # Main UI
    st.title("🛡️ Risk Evaluator")
    st.markdown("---")
    
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

if __name__ == "__main__":
    main()

