import os
import json
import hashlib

METADATA_FILE = "data/metadata.json"

def calculate_file_hash(file_path):
    """Calculates SHA256 hash of a file to detect changes."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_metadata():
    """Loads existing metadata cache."""
    if not os.path.exists(METADATA_FILE):
        return {}
    try:
        with open(METADATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_metadata(metadata):
    """Saves updated metadata cache."""
    os.makedirs(os.path.dirname(METADATA_FILE), exist_ok=True)
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=4)

def update_file_metadata(file_path, category, year, additional_info=None):
    """Updates metadata for a specific file."""
    metadata = load_metadata()
    file_name = os.path.basename(file_path)
    file_hash = calculate_file_hash(file_path)
    
    metadata[file_name] = {
        "category": category,
        "year": year,
        "hash": file_hash,
        "last_updated": os.path.getmtime(file_path)
    }
    if additional_info:
        metadata[file_name].update(additional_info)
        
    save_metadata(metadata)

def get_file_metadata(file_path):
    """Checks if metadata exists and is current (by hash)."""
    file_name = os.path.basename(file_path)
    metadata = load_metadata()
    
    if file_name not in metadata:
        return None
    
    current_hash = calculate_file_hash(file_path)
    if metadata[file_name].get("hash") != current_hash:
        return None
        
    return metadata[file_name]

def find_files_by_category(category, raw_dir="data/raw"):
    """Returns a list of files matching a specific category, sorted by year."""
    metadata = load_metadata()
    results = []
    
    for file_name, data in metadata.items():
        if data.get("category") == category:
            file_path = os.path.join(raw_dir, file_name)
            if os.path.exists(file_path):
                results.append((file_path, data.get("year", 0)))
    
    # Sort by year (descending)
    results.sort(key=lambda x: x[1], reverse=True)
    return results
