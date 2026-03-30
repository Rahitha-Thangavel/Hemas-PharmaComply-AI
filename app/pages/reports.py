import streamlit as st
import os
import sys
import tempfile
import base64
import mimetypes
import shutil
from pathlib import Path

# Add root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.sidebar_clean import render_sidebar
from services.change_detector import compare_gazettes, find_previous_document
from services.file_loader import load_documents
import streamlit.components.v1 as components

def open_file_in_new_tab(file_path):
    """Uses a JavaScript-based Blob object approach to open files in a new tab.
    This is much more reliable for large PDFs/images than simple data URIs.
    """
    if not file_path:
        return
    
    try:
        file_name = os.path.basename(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"
            
        with open(file_path, "rb") as f:
            base64_data = base64.b64encode(f.read()).decode("utf-8")
            
        # Generate HTML/JS to create a Blob and open it in a new window/tab
        # Note: atob() handles base64 decoding in the browser
        html_code = f'''
        <button id="open-document-btn" style="
            display: inline-block;
            padding: 0.5em 1.2em;
            color: #FFFFFF;
            background-color: #003366;
            border-radius: 5px;
            text-decoration: none;
            font-weight: bold;
            border: 1px solid #003366;
            cursor: pointer;
            width: 100%;
            font-family: sans-serif;
            text-align: center;
        ">👁️ Open Final Document ({file_name})</button>

        <script>
            document.getElementById('open-document-btn').onclick = function() {{
                try {{
                    const base64Data = "{base64_data}";
                    const byteCharacters = atob(base64Data);
                    const byteNumbers = new Array(byteCharacters.length);
                    for (let i = 0; i < byteCharacters.length; i++) {{
                        byteNumbers[i] = byteCharacters.charCodeAt(i);
                    }}
                    const byteArray = new Uint8Array(byteNumbers);
                    const blob = new Blob([byteArray], {{type: "{mime_type}"}});
                    const url = URL.createObjectURL(blob);
                    
                    // Open in a new tab
                    const newWindow = window.open(url, '_blank');
                    if (!newWindow) {{
                        alert("Pop-up blocked! Please allow pop-ups for this site to view the document.");
                    }}
                }} catch (e) {{
                    console.error("Error opening document:", e);
                    alert("Failed to open document: " + e.message);
                }}
            }};
        </script>
        '''
        components.html(html_code, height=50)
        
    except Exception as e:
        st.error(f"❌ Could not prepare document for viewing: {e}")

def save_to_data_folder(file_path):
    """Copies a file from temp_uploads to the permanent data/raw folder."""
    if not file_path:
        return None
    
    try:
        # Target directory
        data_raw_dir = os.path.join(project_root, "data", "raw")
        os.makedirs(data_raw_dir, exist_ok=True)
        
        # Target path
        file_name = os.path.basename(file_path)
        target_path = os.path.join(data_raw_dir, file_name)
        
        # Copy file
        shutil.copy(file_path, target_path)
        return target_path
    except Exception as e:
        st.error(f"❌ Failed to save document: {e}")
        return None

def save_uploaded_file(uploaded_file):
    """Save uploaded file to a local project directory instead of system temp."""
    try:
        # Create local upload directory
        upload_dir = os.path.join(project_root, "data", "temp_uploads")
        os.makedirs(upload_dir, exist_ok=True)
        
        # Consistent file path
        file_path = os.path.join(upload_dir, uploaded_file.name)
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        return file_path
    except Exception as e:
        st.error(f"❌ Failed to save uploaded file: {e}")
        return None

def main():
    st.set_page_config(
        page_title="Smart Regulation Change Detector - Hemas PharmaComply AI",
        page_icon="🔄",
        layout="wide"
    )
    
    # Render synchronized sidebar
    render_sidebar()
    
    st.title("🔄 Smart Regulation Change Detector")
    st.markdown("---")
    
    st.info("💡 **Automatically detect changes between your new gazette and the previous version in our database.** "
            "Select a category and upload only the NEW file to see price changes, updates, or deletions.")
    
    # Selection Mode
    mode = st.radio("Choose Comparison Mode:", 
                    ["Auto-select Previous Document (Recommended)", "Manual Upload (Upload Both Files)"],
                    horizontal=True)
    
    # Category Selection
    categories = ["Price Control", "Registration & Fees", "Labelling & Requirements", "Other Regulations"]
    selected_category = st.selectbox("Document Category:", categories)
    
    col1, col2 = st.columns(2)
    
    prev_path = None
    new_file = None
    
    with col1:
        st.subheader("Previous Gazette")
        if "Auto-select" in mode:
            prev_path = find_previous_document(selected_category)
            if prev_path:
                st.success(f"📂 **Found in Database:** {os.path.basename(prev_path)}")
                st.caption(f"Full Path: {prev_path}")
                open_file_in_new_tab(prev_path)
            else:
                st.warning(f"⚠️ No previous document for **'{selected_category}'** found in the database. Please use Manual Upload.")
        else:
            prev_file = st.file_uploader("Upload previous gazette file", type=['pdf', 'docx', 'txt', 'png', 'jpg', 'jpeg'], key="prev_gazette")
            if prev_file:
                prev_path = save_uploaded_file(prev_file)
                if prev_path:
                    open_file_in_new_tab(prev_path)
                    
                    # Option to save permanently to data/raw
                    if st.button("📥 Add this document to Data Folder", key="save_prev", help="Permanently save this file for future comparison"):
                        saved_path = save_to_data_folder(prev_path)
                        if saved_path:
                            st.success(f"✅ Document saved permanently to `data/raw`!")
                            st.balloons()
        
    with col2:
        st.subheader("New Gazette")
        new_file = st.file_uploader("Upload new gazette file", type=['pdf', 'docx', 'txt', 'png', 'jpg', 'jpeg'], key="new_gazette")
        if new_file:
            new_path = save_uploaded_file(new_file)
            if new_path:
                open_file_in_new_tab(new_path)
                
                # Option to save permanently to data/raw
                if st.button("📥 Add this document to Data Folder", help="Permanently save this file for future RAG indexing"):
                    saved_path = save_to_data_folder(new_path)
                    if saved_path:
                        st.success(f"✅ Document saved permanently to `data/raw`!")
                        st.balloons()
                
                # Store in session state for later use during comparison
                st.session_state.temp_new_path = new_path
        
    if st.button("🚀 Detect Changes", use_container_width=True):
        new_path = st.session_state.get('temp_new_path')
        if not prev_path or not new_path:
            st.error("Please ensure both a previous document is selected/uploaded and the new document is uploaded.")
        else:
            try:
                # Perform comparison
                summary = compare_gazettes(prev_path, new_path)
                
                # Clean up temporary new file
                if "temp_uploads" in new_path:
                    os.remove(new_path)
                # Clean up manually uploaded previous file if applicable
                if "Manual" in mode and prev_path and "temp_uploads" in prev_path:
                    os.remove(prev_path)
                
                # Display results
                st.markdown("---")
                st.header("📝 Summary of Regulatory Changes")
                st.markdown(summary)
                
                # Download button
                st.download_button(
                    label="📥 Download Summary",
                    data=summary,
                    file_name=f"regulatory_changes_{selected_category.lower().replace(' ', '_')}.txt",
                    mime="text/plain"
                )
                
            except Exception as e:
                st.error(f"Failed to process files: {str(e)}")

    # Footer/Dashboard Link
    st.markdown("---")
    st.caption("Developed by Hemas PharmaComply AI Core Team | 2025")

if __name__ == "__main__":
    main()
