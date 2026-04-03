import os
import json
import re
import shutil
import time
from pathlib import Path
from services.file_loader import load_documents
from app.core.llm_factory import get_llm
from app.core.config_loader import load_config
from langchain_core.messages import HumanMessage, SystemMessage

METADATA_FILE = os.path.join("data", "metadata.json")

def load_metadata():
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_metadata(metadata):
    os.makedirs("data", exist_ok=True)
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=4)

def analyze_document(file_path):
    """
    Analyzes a document to extract its category and year using LLM.
    Returns (category, year)
    """
    try:
        config = load_config()
        llm = get_llm(config)
        
        # Load only the first few pages/characters
        docs = load_documents([file_path])
        if not docs:
            return "Other Regulations", None
        
        # Extract text for context
        full_text = " ".join([doc.page_content for doc in docs])
        context = full_text[:5000] # Increased context size
        file_name = os.path.basename(file_path)
        
        system_prompt = (
            "You are a regulatory document analyzer for the National Medicines Regulatory Authority (NMRA) of Sri Lanka. "
            "Your task is to identify the CATEGORY and the YEAR of a given gazette or document. "
            "\n\n**CATEGORIES:**"
            "\n- Price Control: Maximum Retail Prices of medicines, price revisions, etc."
            "\n- Registration & Fees: Fees for registration, licensing, renewals of medicines/devices."
            "\n- Labelling & Requirements: Label instructions, clinical trials, GMP, or specific technical requirements."
            "\n- Other Regulations: General acts, public notices, or regulations not fitting above."
            "\n\n**YEAR:**"
            "\nExtract the year of publication or effective date (e.g., 2019, 2023, 2026). "
            "Use both the document text and the filename as hints."
            "\n\n**FORMAT:**"
            "\nReturn ONLY a JSON object like this: {\"category\": \"Price Control\", \"year\": 2026}"
        )
        
        user_content = f"FILENAME: {file_name}\n\nDOCUMENT TEXT SNIPPET:\n{context}\n\nPlease analyze this document."
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_content)
        ]
        
        response = llm.invoke(messages)
        content = response.content if hasattr(response, 'content') else str(response)
        
        # Parse JSON from response
        try:
            # Handle potential markdown formatting in response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                category = result.get("category", "Other Regulations")
                year = result.get("year")
                return category, year
        except:
            pass
            
        return "Other Regulations", None
        
    except Exception as e:
        print(f"Error analyzing document {file_path}: {e}")
        return "Other Regulations", None

def rename_and_update_metadata(file_path, category, year):
    """
    Renames a file in data/raw based on detected category/year and updates metadata.json.
    Prevents redundant prefixing.
    Standard format: Category_Year_OriginalFileName
    """
    try:
        raw_dir = os.path.dirname(file_path)
        old_name = os.path.basename(file_path)
        
        # Clean category for filename
        clean_cat = category.replace(" & ", "_").replace(" ", "-")
        year_str = str(year) if year else "Unknown"
        
        # --- NEW: Strip old prefixes to avoid triple-prefixing ---
        # Pattern matches: Category_Year_ or Category_Unknown_
        prefix_pattern = r'^(Price-Control|Registration_Fees|Labelling_Requirements|Other-Regulations)_(20\d{2}|Unknown)_'
        
        # Repeatedly strip if multiple prefixes exist (edge case)
        stripped_name = old_name
        while re.match(prefix_pattern, stripped_name):
            stripped_name = re.sub(prefix_pattern, '', stripped_name)
            
        new_name = f"{clean_cat}_{year_str}_{stripped_name}"
        new_path = os.path.join(raw_dir, new_name)
        
        # Perform rename
        if file_path != new_path:
            # If target exists, maybe append timestamp
            if os.path.exists(new_path) and Path(file_path).resolve() != Path(new_path).resolve():
                name_parts = os.path.splitext(new_name)
                new_name = f"{name_parts[0]}_{int(time.time())}{name_parts[1]}"
                new_path = os.path.join(raw_dir, new_name)
            
            # Use os.rename instead of shutil.move if on same drive, safer
            os.rename(file_path, new_path)
        
        # Update metadata
        metadata = load_metadata()
        
        # Remove old key if name changed
        if old_name in metadata and old_name != new_name:
            del metadata[old_name]
            
        metadata[new_name] = {
            "original_name": stripped_name,
            "category": category,
            "year": year,
            "analyzed_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        save_metadata(metadata)
        
        return new_path
        
    except Exception as e:
        print(f"Error renaming file {file_path}: {e}")
        return file_path

def sync_all_documents(overwrite=False):
    """
    Analyzes all documents in data/raw. 
    If overwrite is False, skips files already in metadata.json.
    """
    raw_dir = os.path.join("data", "raw")
    if not os.path.exists(raw_dir):
        return 0
    
    # Get physical files
    files = [f for f in os.listdir(raw_dir) if os.path.isfile(os.path.join(raw_dir, f))]
    count = 0
    
    metadata = load_metadata()
    
    # Also clean up metadata entries for files that no longer exist
    existing_meta_keys = list(metadata.keys())
    for key in existing_meta_keys:
        if key not in files:
            del metadata[key]
    save_metadata(metadata)
    
    for fname in files:
        fpath = os.path.join(raw_dir, fname)
        
        # Skip if already analyzed (unless overwrite is True)
        if not overwrite and fname in metadata:
            continue
            
        # Analyze and rename
        category, year = analyze_document(fpath)
        rename_and_update_metadata(fpath, category, year)
        count += 1
        
    return count
