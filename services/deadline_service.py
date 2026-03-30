import os
import json
import re
from datetime import datetime
from pathlib import Path
from pypdf import PdfReader
import logging

logger = logging.getLogger(__name__)

DB_PATH = Path("data/deadlines_db.json")

def initialize_db():
    if not DB_PATH.exists():
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump([], f)

def load_deadlines():
    initialize_db()
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_deadlines(deadlines):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(deadlines, f, indent=4)

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    except Exception as e:
        logger.error(f"Error reading {pdf_path}: {e}")
    return text

def parse_deadlines_from_text(text, source_file):
    """
    Dummy/Regex implementation to extract dates. 
    In a real scenario, an LLM call could be placed here.
    """
    deadlines = []
    # Match dates like YYYY-MM-DD or DD/MM/YYYY
    date_patterns = [
        r'\b(202[0-9]-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01]))\b',
        r'\b(?:0[1-9]|[12][0-9]|3[01])/(?:0[1-9]|1[0-2])/(202[0-9])\b'
    ]
    
    lines = text.split("\n")
    for i, line in enumerate(lines):
        for pattern in date_patterns:
            matches = re.finditer(pattern, line)
            for match in matches:
                date_str = match.group(0)
                # Normalize date
                try:
                    if "/" in date_str:
                        d, m, y = date_str.split("/")
                        parsed_date = datetime(int(y), int(m), int(d))
                    else:
                        parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
                        
                    # Extract context (current line + next line if exists)
                    context = line.strip()
                    if i + 1 < len(lines):
                        context += " " + lines[i+1].strip()
                        
                    # Only add if it looks like a deadline context (basic heuristic)
                    action_note = "Review compliance requirements for this date."
                    if "implement" in context.lower() or "effective" in context.lower() or "price" in context.lower():
                        action_note = "Price implementation / effective date reached."
                    elif "license" in context.lower() or "renew" in context.lower():
                        action_note = "License renewal / submission required."
                        
                    deadlines.append({
                        "id": f"{source_file}_{len(deadlines)}",
                        "source": source_file,
                        "date": parsed_date.strftime("%Y-%m-%d"),
                        "context": context[:200] + "..." if len(context) > 200 else context,
                        "action": action_note
                    })
                except Exception as e:
                    logger.warning(f"Could not parse date {date_str}: {e}")
                    
    return deadlines

def sync_deadlines(data_dir):
    """
    Scans data_dir for PDFs and extracts deadlines.
    """
    initialize_db()
    existing = load_deadlines()
    existing_sources = {d["source"] for d in existing}
    
    new_deadlines_found = []
    
    pdf_files = list(Path(data_dir).rglob("*.pdf"))
    for pdf_file in pdf_files:
        filename = pdf_file.name
        if filename not in existing_sources:
            text = extract_text_from_pdf(str(pdf_file))
            extracted = parse_deadlines_from_text(text, filename)
            if extracted:
                new_deadlines_found.extend(extracted)
                existing.extend(extracted)
                
    save_deadlines(existing)
    return len(new_deadlines_found)

def get_status(deadline_date_str):
    try:
        deadline = datetime.strptime(deadline_date_str, "%Y-%m-%d")
        days_remaining = (deadline - datetime.now()).days
        
        if days_remaining <= 1:
            return "Red", days_remaining
        elif 1 < days_remaining <= 7:
            return "Yellow", days_remaining
        else:
            return "Green", days_remaining
    except:
        return "Unknown", 0

def send_email_reminders():
    """
    Simulates sending emails for deadlines that are exactly 7 days or 1 day away.
    """
    deadlines = load_deadlines()
    emails_sent = []
    for d in deadlines:
        color, days = get_status(d["date"])
        if days == 7:
            emails_sent.append(f"Email sent (7 days remaining) for {d['source']} ({d['date']})")
        elif days == 1:
            emails_sent.append(f"Email sent (1 day remaining) for {d['source']} ({d['date']}) - URGENT!")
            
    return emails_sent
