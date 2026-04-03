import os
import sys
import yaml
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add the project root to the python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.core.config_loader import load_config
from app.core.chatbot import HemasPharmaComplyAI
from utils.sidebar_clean import render_sidebar, run_nmra_sync
from services.history_manager import HistoryManager

def inject_dashboard_css():
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #001f3f 0%, #003366 100%);
        color: white;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    .hero-title {
        font-size: 3rem !important;
        font-weight: 800 !important;
        color: white !important;
        margin-bottom: 0.5rem !important;
    }
    .hero-subtitle {
        font-size: 1.2rem;
        color: #E2E8F0;
        opacity: 0.9;
    }
    .feature-card {
        background-color: white;
        padding: 2rem;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        text-align: center;
        transition: all 0.3s ease;
        cursor: pointer;
        height: 250px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        border-color: #3b82f6;
    }
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    .feature-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #003366;
        margin-bottom: 0.5rem;
    }
    .feature-desc {
        font-size: 0.9rem;
        color: #64748b;
    }
    .sync-section {
        background: #F0F9FF;
        padding: 2rem;
        border-radius: 12px;
        text-align: center;
        margin: 2rem 0;
        border: 1px dashed #0EA5E9;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    st.set_page_config(
        page_title="Dashboard - Hemas PharmaComply AI",
        page_icon="🛡️",
        layout="wide"
    )

    # 1. IMMEDIATE UI RENDERING (Ensures branded sidebar shows during loading)
    render_sidebar()
    inject_dashboard_css()

    # 2. INITIALIZATION
    if 'history_manager' not in st.session_state:
        st.session_state.history_manager = HistoryManager()

    if 'chatbot' not in st.session_state:
        with st.container():
            st.markdown("<br><br><br>", unsafe_allow_html=True)
            col_l, col_c, col_r = st.columns([0.05, 0.9, 0.05])
            with col_c:
                st.markdown("<h2 style='text-align: center; color: #003366;'>🚀 Initializing PharmaComply AI...</h2>", unsafe_allow_html=True)
                with st.status("Loading knowledge base and regulatory engines...", expanded=True) as status:
                    try:
                        config = load_config()
                        st.session_state.chatbot = HemasPharmaComplyAI(config)
                        status.update(label="✅ System Ready!", state="complete")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Initialization failed: {str(e)}")
                        return

    # 3. DASHBOARD CONTENT (Rendered after Init)

    # --- HERO SECTION ---
    st.markdown(f"""
    <div class="main-header">
        <h1 class="hero-title">Welcome to PharmaComply AI</h1>
        <p class="hero-subtitle">Your intelligent hub for NMRA regulatory monitoring and business impact intelligence.</p>
    </div>
    """, unsafe_allow_html=True)

    # --- ACTION CENTER ---
    st.divider()
    st.markdown("<h3 style='text-align: center; color: #003366;'>🔄 NMRA Synchronization Center</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748b;'>Synchronize your local library with the live NMRA Gazette database to ensure compliance with the latest regulations.</p>", unsafe_allow_html=True)
    
    col_s1, col_s2, col_s3 = st.columns([1, 1.5, 1])
    with col_s2:
        if st.button("🚀 SYNC WITH NMRA NOW", key="dash_sync_btn", type="primary", use_container_width=True):
            run_nmra_sync()
        
        # PROMINENT LIVE FEEDBACK
        if st.session_state.get("sync_message"):
            st.success(st.session_state.sync_message)
            # Clear it after showing once? Or keep it? 
            # Let's keep it until next interaction.
        
        last_sync = st.session_state.get("last_sync", "Never")
        st.markdown(f"<p style='text-align: center; font-size: 0.8rem; color: #94a3b8;'>Status: Live Connected | Last Live Scan: {last_sync}</p>", unsafe_allow_html=True)
    
    st.divider()

    # --- FEATURE GRID ---
    st.markdown("## 🎯 Feature Modules")
    st.markdown("Explore your regulatory capabilities below.")
    
    # Grid Row 1
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">💬</div>
            <div class="feature-title">Q&A Assistant</div>
            <p class="feature-desc">Deep regulatory search. Ask questions and get cited answers from your entire library.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Q&A", key="nav_qa", use_container_width=True):
            st.switch_page("pages/1_qa_assistant.py")

    with c2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <div class="feature-title">Impact Predictor</div>
            <p class="feature-desc">Predict how new gazette price changes affect your current product portfolio.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Predictor", key="nav_impact", use_container_width=True):
            st.switch_page("pages/impact_analysis.py")

    with c3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🔄</div>
            <div class="feature-title">Change Detector</div>
            <p class="feature-desc">Automatically compare new and old price lists to identify exact value shifts.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Detector", key="nav_reports", use_container_width=True):
            st.switch_page("pages/reports.py")

    # Grid Row 2
    st.markdown("<br>", unsafe_allow_html=True)
    c4, c5, c6 = st.columns(3)

    with c4:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📅</div>
            <div class="feature-title">Deadline Tracker</div>
            <p class="feature-desc">Monitor implementation deadlines and set critical compliance alerts.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Dash", key="nav_dash", use_container_width=True):
            st.switch_page("pages/dashboard.py")

    with c5:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🛡️</div>
            <div class="feature-title">Risk Evaluator</div>
            <p class="feature-desc">Verify if proposed pharmaceutical actions comply with existing regulations.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Evaluator", key="nav_compl", use_container_width=True):
            st.switch_page("pages/compliance_checker.py")
    
    with c6:
        # Mini Stats Card
        files = list(Path("data").rglob("*.pdf"))
        st.markdown(f"""
        <div class="feature-card" style="background-color: #F8FAFC;">
            <div class="feature-icon">📦</div>
            <div class="feature-title">Library Status</div>
            <p class="feature-desc">Total Active Documents: <b>{len(files)}</b><br>AI Model: <b>Groq (Llama 3.3)</b></p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown("<p style='text-align: center; color: #64748b;'>© 2026 Hemas Holdings PLC | Regulatory Intelligence Unit</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
