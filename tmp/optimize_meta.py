import os
import sys
import json

# Add root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from services.categorizer import analyze_document, rename_and_update_metadata
    
    METADATA_FILE = os.path.join("data", "metadata.json")
    with open(METADATA_FILE, "r") as f:
        metadata = json.load(f)
    
    raw_dir = os.path.join("data", "raw")
    
    print("Re-analyzing files with 'Unknown' years...")
    for fname, meta in list(metadata.items()):
        if meta.get("year") is None or meta.get("year") == "Unknown":
            old_path = os.path.join(raw_dir, fname)
            if os.path.exists(old_path):
                print(f"Analyzing {fname}...")
                category, year = analyze_document(old_path)
                if year:
                    print(f"Found year: {year}")
                    new_path = rename_and_update_metadata(old_path, category, year)
                    # Remove old entry if renamed
                    new_fname = os.path.basename(new_path)
                    if new_fname != fname:
                        del metadata[fname]
    
    print("Optimization complete.")
except Exception as e:
    print(f"Error during optimization: {e}")
