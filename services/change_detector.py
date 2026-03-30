import streamlit as st
import os
import glob
from app.core.llm_factory import get_llm
from app.core.config_loader import load_config
from services.file_loader import load_documents
from langchain_core.messages import HumanMessage, SystemMessage

from services.metadata_manager import find_files_by_category

def find_previous_document(category):
    """
    Uses the metadata manager to find the most relevant previous gazette 
    based on contextual category and actual year extracted.
    """
    raw_dir = os.path.join("data", "raw")
    
    # Get files in category sorted by year (descending)
    matches = find_files_by_category(category, raw_dir)
    
    if not matches:
        # Fallback to simple keyword search if metadata is missing/incomplete
        # This handles cases where files haven't been indexed/analyzed yet
        keyword_map = {
            "Price Control": ["price", "maximum", "nmra", "essential"],
            "Registration & Fees": ["fees", "registration", "licensing"],
            "Labelling & Requirements": ["labelling", "label", "amendment"],
            "Other Regulations": ["regulation", "act", "nmra"]
        }
        keywords = keyword_map.get(category, [])
        if not keywords: return None
        
        files = glob.glob(os.path.join(raw_dir, "*.*"))
        fallback_matches = []
        for f in files:
            if any(kw in os.path.basename(f).lower() for kw in keywords):
                fallback_matches.append((f, os.path.getmtime(f)))
        
        if not fallback_matches: return None
        fallback_matches.sort(key=lambda x: x[1], reverse=True)
        return fallback_matches[0][0]

    # Return the latest year's file
    # (Matches are already sorted by year descending by find_files_by_category)
    return matches[0][0]

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
