import os
import sys
from pathlib import Path

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from services.file_loader import load_documents
from app.core.config_loader import load_config

def test_page_mapping():
    try:
        config = load_config()
        data_dir = Path(config["paths"]["data_dir"])
        pdf_files = list(data_dir.glob("*.pdf"))
        
        if not pdf_files:
            print("No PDF files found to test.")
            return

        test_file = str(pdf_files[0])
        print(f"Testing with: {test_file}")
        
        docs = load_documents([test_file])
        
        # Check first 20 docs for page variability
        pages = [doc.metadata.get("page") for doc in docs[:50]]
        unique_pages = sorted(list(set(pages)))
        
        print(f"Total chunks: {len(docs)}")
        print(f"Unique pages found: {unique_pages}")
        
        if len(unique_pages) > 1:
            print("SUCCESS: Multiple pages detected.")
        else:
            print("WARNING: Only one page detected. If the file is multi-page, this is an issue.")

        for i, doc in enumerate(docs[:10]):
            print(f"Chunk {i}: Source={doc.metadata.get('source')}, Page={doc.metadata.get('page')}")

    except Exception as e:
        print(f"Error during test: {e}")

if __name__ == "__main__":
    test_page_mapping()
