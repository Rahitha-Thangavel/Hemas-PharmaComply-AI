import streamlit as st
import os
import glob
import re
from app.core.llm_factory import get_llm
from app.core.config_loader import load_config
from services.file_loader import load_documents
from langchain_core.messages import HumanMessage, SystemMessage
from services.categorizer import load_metadata

def list_all_documents_in_category(category):
    """
    Returns a list of all documents in data/raw that match the specified category.
    Returns: List of dicts [{"path": "...", "name": "...", "year": ...}]
    Sorted by year (descending)
    """
    raw_dir = os.path.join("data", "raw")
    if not os.path.exists(raw_dir):
        return []

    metadata = load_metadata()
    files = glob.glob(os.path.join(raw_dir, "*.*"))
    
    matches = []
    seen_paths = set()
    
    # 1. Check metadata
    for f in files:
        fname = os.path.basename(f)
        if fname in metadata:
            file_meta = metadata[fname]
            if file_meta.get("category") == category:
                year = file_meta.get("year") or 0
                matches.append({
                    "path": f, 
                    "name": fname, 
                    "year": year, 
                    "mtime": os.path.getmtime(f),
                    "original_name": file_meta.get("original_name", fname)
                })
                seen_paths.add(f)

    # 2. Fallback to keyword matching for untracked files
    keyword_map = {
        "Price Control": ["price", "maximum", "nmra", "essential"],
        "Registration & Fees": ["fees", "registration", "licensing"],
        "Labelling & Requirements": ["labelling", "label", "amendment"],
        "Other Regulations": ["regulation", "act", "nmra"]
    }
    keywords = keyword_map.get(category, [])
    
    if keywords:
        for f in files:
            if f in seen_paths:
                continue
            fname = os.path.basename(f)
            fname_lower = fname.lower()
            if any(kw in fname_lower for kw in keywords):
                year_match = re.search(r'(20\d{2})', fname)
                year = int(year_match.group(1)) if year_match else 0
                matches.append({
                    "path": f, 
                    "name": fname, 
                    "year": year, 
                    "mtime": os.path.getmtime(f),
                    "original_name": fname
                })

    # Sort: Year (desc), Mtime (desc)
    matches.sort(key=lambda x: (x["year"] if x["year"] else 0, x["mtime"]), reverse=True)
    return matches

def find_previous_document(category):
    """
    Finds the single latest document for a category.
    """
    docs = list_all_documents_in_category(category)
    if docs:
        return docs[0]["path"]
    return None

def find_comparison_pair(new_file_path):
    """
    Given a new file, identifies its category and year, 
    then finds the most appropriate previous version for comparison.
    Returns: (prev_path, new_path) or (None, new_path)
    """
    metadata = load_metadata()
    fname = os.path.basename(new_file_path)
    
    # 1. Get info about the new file
    category = "Other Regulations"
    year = 0
    if fname in metadata:
        category = metadata[fname].get("category", "Other Regulations")
        year = metadata[fname].get("year") or 0
    else:
        # Fallback to name parsing
        year_match = re.search(r'(20\d{2})', fname)
        year = int(year_match.group(1)) if year_match else 0
        
        # Simple category guess if not in metadata
        if "price" in fname.lower() or "mrp" in fname.lower():
            category = "Price Control"
    
    # 2. List all in category
    all_in_cat = list_all_documents_in_category(category)
    
    # 3. Filter out the new file itself
    previous_candidates = [d for d in all_in_cat if d["path"] != new_file_path]
    
    # 4. Find the best match (next oldest year or most recently modified that isn't the new one)
    if previous_candidates:
        # Since list_all_documents_in_category is already sorted by Year desc, Mtime desc
        # the first one in the list that is older than the current year (or the first one in list if years match) is best.
        for cand in previous_candidates:
            if cand["year"] <= year:
                return cand["path"], new_file_path
        
        # If all are somehow newer, take the most recent one anyway
        return previous_candidates[0]["path"], new_file_path
        
    return None, new_file_path

def compare_gazettes(file_path1, file_path2):
    """
    Compares two pharmaceutical gazette files and returns a summary of changes.
    """
    try:
        # Load configuration
        config = load_config()
        llm = get_llm(config)

        # Load documents
        with st.status("Reading documents...") as status:
            st.write(f"Loading {file_path1}...")
            docs1 = load_documents([file_path1])
            st.write(f"Loading {file_path2}...")
            docs2 = load_documents([file_path2])
            status.update(label="Documents loaded ✅", state="complete")

        if not docs1:
            return (f"❌ Error: Could not load the PREVIOUS document ({file_path1}).\n\n"
                    "**Potential issues:**\n"
                    "- The file might be a **scanned image** (no digital text) and OCR failed.\n"
                    "- The file might be corrupted or protected by a password.\n"
                    "- Please ensure it's a standard, readable PDF, Image, DOCX, or TXT file.")
        
        if not docs2:
            return (f"❌ Error: Could not load the NEW document ({file_path2}).\n\n"
                    "**Potential issues:**\n"
                    "- The file might be a **scanned image** (no digital text) and OCR failed.\n"
                    "- The file might be corrupted or protected by a password.\n"
                    "- Please ensure it's a standard, readable PDF, Image, DOCX, or TXT file.")

        # Extract text
        text1 = " ".join([doc.page_content for doc in docs1])
        text2 = " ".join([doc.page_content for doc in docs2])

        # Show extracted text to user for verification
        with st.expander("🔍 View Extracted Text (Comparison Preview)"):
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("Previous Gazette")
                st.text_area("Content from File 1", text1[:1000] + ("..." if len(text1) > 1000 else ""), height=200, disabled=True)
            with col_b:
                st.subheader("New Gazette")
                st.text_area("Content from File 2", text2[:1000] + ("..." if len(text2) > 1000 else ""), height=200, disabled=True)

        # Limit text size for LLM context (simple truncation for now)
        # In a more advanced version, we could use RAG or a map-reduce approach
        max_chars = 15000 
        if len(text1) > max_chars:
            text1 = text1[:max_chars] + "... [Truncated]"
        if len(text2) > max_chars:
            text2 = text2[:max_chars] + "... [Truncated]"

        # Prepare prompt
        system_prompt = (
            "You are a pharmaceutical regulatory expert specializing in NMRA (National Medicines Regulatory Authority) price gazettes. "
            "Your task is to compare a PREVIOUS gazette and a NEW gazette. "
            "Identify ALL changes, especially: "
            "1. Price increases or decreases (list the medicine name and the old vs new price). "
            "2. New medicines added to the list. "
            "3. Medicines removed from the list. "
            "4. Changes in dosage, form, or manufacturer details. "
            "\n\n**RESPONSE FORMAT:**"
            "\nIf you find price differences, you MUST provide a markdown table summary with these columns:"
            "\n| Generic Name | Strength | Previous Price | New Price | Change (%) |"
            "\n\nFollow the table with a bullet-pointed summary of other qualitative changes (additions, removals, dosage changes)."
        )

        user_content = (
            f"PREVIOUS GAZETTE TEXT:\n{text1}\n\n"
            f"NEW GAZETTE TEXT:\n{text2}\n\n"
            "Please generate the bullet-point summary of changes."
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_content)
        ]

        # Get response from LLM
        with st.status("Analyzing changes with AI...") as status:
            st.write("Prompting LLM...")
            response = llm.invoke(messages)
            summary = response.content if hasattr(response, 'content') else str(response)
            status.update(label="Analysis complete! ✅", state="complete")

        return summary

    except Exception as e:
        return f"❌ Error during comparison: {str(e)}"
