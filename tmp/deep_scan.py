import os
import sys

# Add root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from services.categorizer import sync_all_documents
    print("Starting DEEP SCAN of documents in data/raw...")
    count = sync_all_documents(overwrite=True)
    print(f"Deep Scan complete. Processed {count} documents.")
except Exception as e:
    print(f"Error during Deep Scan: {e}")
    import traceback
    traceback.print_exc()
