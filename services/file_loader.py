import time
import os
from pathlib import Path
import streamlit as st
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
    UnstructuredPDFLoader
)
try:
    import pytesseract
    from pdf2image import convert_from_path
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

from langchain_core.documents import Document

# Configure Tesseract Path (for Windows)
TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
if os.path.exists(TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

def perform_ocr_on_image(file_path):
    """
    Performs OCR directly on an image file.
    """
    if not OCR_AVAILABLE:
        st.error("❌ OCR Error: Required Python library (pytesseract) is not installed.")
        return []

    try:
        from PIL import Image
        st.info("🔄 Running OCR on image...")
        image = Image.open(file_path)
        page_text = pytesseract.image_to_string(image)
        
        if not page_text.strip():
            return []
            
        return [Document(page_content=page_text, metadata={"source": os.path.basename(file_path), "method": "ocr"})]
    except Exception as e:
        st.error(f"❌ Image OCR failed: {e}")
        return []

def perform_ocr(file_path):
    """
    Converts PDF pages to images and performs OCR using Tesseract.
    """
    if not OCR_AVAILABLE:
        st.error("❌ OCR Error: Required Python libraries (pytesseract, pdf2image) are not installed.")
        st.info("💡 Please run: `pip install pytesseract pdf2image pillow` in your terminal.")
        return []

    try:
        with st.status("🔄 Digital text not found. Running OCR...") as status:
            st.write("Converting PDF pages to images...")
            # Convert PDF to list of PIL images
            images = convert_from_path(file_path)
            
            all_text = ""
            for i, image in enumerate(images):
                st.write(f"Processing page {i+1}/{len(images)}...")
                page_text = pytesseract.image_to_string(image)
                all_text += f"\n--- Page {i+1} ---\n{page_text}"
            
            status.update(label="OCR complete! ✅", state="complete")
            
            if not all_text.strip():
                return []
                
            return [Document(page_content=all_text, metadata={"source": os.path.basename(file_path), "method": "ocr"})]
    except Exception as e:
        st.error(f"❌ OCR failed: {e}")
        st.info("💡 Tip: Ensure Tesseract and Poppler are installed and in your System PATH.")
        return []

def load_documents(file_paths):
    all_docs = []
    for file_path in file_paths:
        try:
            file_name = Path(file_path).name
            # Case-insensitive check for file extensions
            ext = Path(file_path).suffix.lower()
            
            if not Path(file_path).exists():
                st.error(f"❌ File not found: {file_path}")
                docs = []
            
            elif os.path.getsize(file_path) == 0:
                st.error(f"❌ File is empty (0 bytes): {file_path}")
                docs = []
            
            elif ext == '.pdf':
                # Try PyPDFLoader first (more standard on Windows)
                try:
                    loader = PyPDFLoader(file_path)
                    docs = loader.load()
                    if docs:
                        st.info(f"✅ Loaded {len(docs)} pages from {file_name}")
                    else:
                        st.warning(f"⚠️ No text content found in {file_name}. Attempting OCR fallback...")
                        docs = perform_ocr(file_path)
                except Exception as e:
                    st.info(f"🔄 PyPDFLoader failed for {file_name}, trying fallbacks... ({e})")
                    try:
                        loader = UnstructuredPDFLoader(file_path, mode="elements")
                        docs = loader.load()
                        st.info(f"✅ Loaded {len(docs)} fragments via Unstructured.")
                    except:
                        docs = []
            
            elif ext == '.txt':
                loader = TextLoader(file_path, encoding='utf-8')
                docs = loader.load()
                st.info(f"✅ Loaded text file: {file_name} ({len(docs[0].page_content)} characters)")
            
            elif ext in ('.docx', '.doc'):
                loader = Docx2txtLoader(file_path)
                docs = loader.load()
                st.info(f"✅ Loaded Word document: {file_name}")
            
            elif ext in ('.png', '.jpg', '.jpeg', '.tiff'):
                docs = perform_ocr_on_image(file_path)
                if docs:
                    st.info(f"✅ Loaded image via OCR: {file_name}")
                else:
                    st.warning(f"⚠️ Could not extract text from image: {file_name}")
            
            else:
                st.warning(f"⚠️ Unsupported file type: {ext}")
                docs = []
            
            for doc in docs:
                doc.metadata.update({
                    "source": file_name,
                    "file_path": file_path,
                    "file_type": ext[1:].upper(),
                    "loaded_at": time.strftime("%Y-%m-%d %H:%M:%S")
                })
            
            all_docs.extend(docs)
                
        except Exception as e:
            st.error(f"❌ Unexpected error loading {file_path}: {e}")
            
    return all_docs