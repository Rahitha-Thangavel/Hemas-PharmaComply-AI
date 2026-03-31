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
from langchain.schema import Document

# Optional imports for OCR
try:
    import pytesseract
    import pypdfium2
    from PIL import Image
    HAS_OCR = True
    
    # Auto-detect Tesseract binary path on Windows if not in PATH
    TESS_PATHS = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe".format(os.getenv("USERNAME", "default"))
    ]
    for path in TESS_PATHS:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            break
except ImportError:
    HAS_OCR = False

def ocr_pdf(file_path):
    """Fallback OCR method for scanned PDFs using pypdfium2 (No Poppler required)."""
    if not HAS_OCR:
        st.warning("⚠️ OCR libraries (pytesseract, pypdfium2) not installed. Unable to process scanned PDF.")
        return []
    
    try:
        # Check if tesseract binary is actually found
        try:
            pytesseract.get_tesseract_version()
        except Exception:
            st.error("❌ Tesseract OCR binary not found on your system.")
            st.markdown("""
            ### 🛠️ How to fix Tesseract (Method A):
            1. **Download:** [Tesseract 64-bit Installer](https://github.com/UB-Mannheim/tesseract/wiki)
            2. **Install:** Run the `.exe` and note the installation path.
            3. **Path:** Add the installation folder (e.g., `C:\\Program Files\\Tesseract-OCR`) to your **System Environment Variables (PATH)**.
            4. **Restart:** Refresh streamlit and try again.
            """)
            return []

        # Convert PDF pages to images using pypdfium2 (NO POPPLER REQUIRED)
        pdf = pypdfium2.PdfDocument(file_path)
        
        page_docs = []
        for i in range(len(pdf)):
            # Render page to image (Pillow format)
            page = pdf[i]
            bitmap = page.render(scale=2)  # High-res for OCR
            pil_image = bitmap.to_pil()
            
            # Extract text using Tesseract
            page_text = pytesseract.image_to_string(pil_image)
            
            # Clean text: remove excessive whitespace and messy characters
            clean_text = "\n".join([line.strip() for line in page_text.split("\n") if line.strip()])
            
            if clean_text:
                page_docs.append(Document(
                    page_content=clean_text, 
                    metadata={
                        "source": Path(file_path).name, 
                        "page": i + 1,  # Store actual page number (1-indexed)
                        "is_ocr": True
                    }
                ))
            
        return page_docs
    except Exception as e:
        st.error(f"❌ OCR processing failed for {file_path}: {e}")
        return []

def load_documents(file_paths):
    all_docs = []
    for file_path in file_paths:
        try:
            file_name = Path(file_path).name
            docs = []
            
            if file_path.endswith('.pdf'):
                # Try standard loaders first
                try:
                    loader = UnstructuredPDFLoader(file_path, mode="elements")
                    docs = loader.load()
                except Exception:
                    try:
                        loader = PyPDFLoader(file_path)
                        docs = loader.load()
                    except Exception:
                        docs = []
                
                # Smart Detection: If extracted text is suspiciously short, it might be a scanned PDF
                total_text_len = sum(len(doc.page_content) for doc in docs)
                if total_text_len < 100:  # Threshold for "empty" or scanned document
                    st.info(f"🔍 Scanned PDF detected: {file_name}. Attempting OCR...")
                    ocr_docs = ocr_pdf(file_path)
                    if ocr_docs:
                        docs = ocr_docs
                    elif not docs:
                        st.warning(f"⚠️ No text could be extracted from {file_name}")
            
            elif file_path.endswith('.txt'):
                try:
                    loader = TextLoader(file_path, encoding='utf-8')
                    docs = loader.load()
                except UnicodeDecodeError:
                    loader = TextLoader(file_path, encoding='latin-1')
                    docs = loader.load()
            
            elif file_path.endswith(('.docx', '.doc')):
                try:
                    loader = Docx2txtLoader(file_path)
                    docs = loader.load()
                except Exception as e:
                    st.warning(f"⚠️ Failed to load DOCX {file_name}: {e}")
            
            # Standardize Metadata
            for doc in docs:
                # 1. Standardize page indexing (PyPDFLoader is 0-indexed, OCR is 1-indexed)
                if "page_number" in doc.metadata:
                    # Unstructured mode="elements" uses 1-indexed page_number
                    try:
                        doc.metadata["page"] = int(doc.metadata["page_number"])
                    except (ValueError, TypeError):
                        doc.metadata["page"] = 1
                elif "page" in doc.metadata:
                    try:
                        p_val = int(doc.metadata["page"])
                        # Standard loaders (PyPDF) are 0-indexed. OCR is already 1-indexed.
                        if not doc.metadata.get("is_ocr", False):
                            doc.metadata["page"] = p_val + 1
                    except (ValueError, TypeError):
                        doc.metadata["page"] = 1
                else:
                    # Default for non-paginated docs (text, docx)
                    doc.metadata["page"] = 1


                doc.metadata.update({
                    "source": file_name,
                    "file_path": file_path,
                    "file_type": Path(file_path).suffix[1:].upper(),
                    "loaded_at": time.strftime("%Y-%m-%d %H:%M:%S")
                })
            
            all_docs.extend(docs)
                
        except Exception as e:
            st.warning(f"⚠️ Unexpected error loading {file_path}: {e}")
            
    return all_docs
