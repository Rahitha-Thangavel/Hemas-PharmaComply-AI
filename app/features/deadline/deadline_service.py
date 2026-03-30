import os
import json
import re
from datetime import datetime
from pathlib import Path
from pypdf import PdfReader
import logging

logger = logging.getLogger(__name__)

# Base directory of the project (assuming this file is in app/features/deadline/core.py)
# But we'll just use relative to CWD if we run from root
DB_PATH = Path("data/deadlines_db.json")

def initialize_db():
    if not DB_PATH.exists():
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump([], f)

def load_deadlines():
    initialize_db()
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

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
    Robust extraction of deadlines using regex and keyword context.
    """
    deadlines = []
    
    # Date patterns
    date_patterns = [
        # YYYY-MM-DD
        r'\b(202[0-9]-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01]))\b',
        # DD/MM/YYYY
        r'\b(?:0[1-9]|[12][0-9]|3[01])/(?:0[1-9]|1[0-2])/(202[0-9])\b',
        # Month DD, YYYY or DD Month YYYY
        r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+202\d\b',
        r'\b\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+202\d\b'
    ]
    
    # Keywords that indicate a deadline or regulatory action
    keywords = {
        "price": "Price implementation / revision deadline.",
        "effective": "Regulation effective date reached.",
        "license": "License renewal / application required.",
        "renew": "Renewal submission deadline.",
        "expiry": "Document / License expiry date.",
        "submit": "Submission deadline for compliance.",
        "implement": "Implementation required by this date.",
        "gazette": "Gazette notification compliance date.",
        "maximum": "Maximum retail price implementation.",
        "nmra": "NMRA regulatory requirement deadline."
    }
    
    lines = text.split("\n")
    for i, line in enumerate(lines):
        for pattern in date_patterns:
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                date_str = match.group(0)
                
                # Normalize date
                parsed_date = None
                try:
                    if "/" in date_str:
                        parts = date_str.split("/")
                        if len(parts[0]) == 4: # YYYY/MM/DD
                            parsed_date = datetime.strptime(date_str, "%Y/%m/%d")
                        else: # DD/MM/YYYY
                            parsed_date = datetime.strptime(date_str, "%d/%m/%Y")
                    elif "-" in date_str:
                        parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
                    else:
                        # Handle "March 21, 2025" or "21 March 2025"
                        clean_date = date_str.replace(",", "")
                        try:
                            parsed_date = datetime.strptime(clean_date, "%B %d %Y")
                        except ValueError:
                            try:
                                parsed_date = datetime.strptime(clean_date, "%d %B %Y")
                            except ValueError:
                                # Short months
                                for fmt in ["%b %d %Y", "%d %b %Y"]:
                                    try:
                                        parsed_date = datetime.strptime(clean_date, fmt)
                                        break
                                    except ValueError:
                                        continue
                except Exception as e:
                    logger.warning(f"Failed to parse date string '{date_str}': {e}")
                    continue

                if not parsed_date:
                    continue
                
                # Context window: 2 lines before, current line, 2 lines after
                start_idx = max(0, i - 2)
                end_idx = min(len(lines), i + 3)
                context_chunk = " ".join([l.strip() for l in lines[start_idx:end_idx]])
                
                # Heuristic scoring/classification
                action_note = "Review compliance requirements."
                found_keyword = False
                
                lower_context = context_chunk.lower()
                for kw, note in keywords.items():
                    if kw in lower_context:
                        action_note = note
                        found_keyword = True
                        break
                
                # Importance check: If it has keywords OR is a future date, we keep it
                # We avoid keeps historical dates unless they have strong keywords
                is_future = parsed_date >= datetime.now()
                
                if found_keyword or is_future:
                    deadlines.append({
                        "id": f"{source_file}_{len(deadlines)}_{parsed_date.strftime('%Y%m%d')}",
                        "source": source_file,
                        "date": parsed_date.strftime("%Y-%m-%d"),
                        "context": context_chunk[:250] + "..." if len(context_chunk) > 250 else context_chunk,
                        "action": action_note,
                        "confidence": "High" if found_keyword else "Medium"
                    })
                    
    # Deduplicate within the same file (same date, same note)
    unique_deadlines = []
    seen = set()
    for d in deadlines:
        key = (d["date"], d["action"])
        if key not in seen:
            unique_deadlines.append(d)
            seen.add(key)
            
    return unique_deadlines

def sync_deadlines(data_dir):
    """
    Scans data_dir for PDFs and extracts deadlines.
    """
    initialize_db()
    existing = load_deadlines()
    existing_sources = {d["source"] for d in existing}
    
    new_deadlines_found = []
    
    # scan both root and subdirectories (rglob)
    pdf_files = list(Path(data_dir).rglob("*.pdf"))
    for pdf_file in pdf_files:
        filename = pdf_file.name
        # Even if source exists, we might want to check if new deadlines can be extracted
        # But for efficiency, we usually skip processed files.
        # However, user wants to scan ALL PDFs in data/raw.
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
        
        if days_remaining < 0:
            return "Overdue", days_remaining
        elif days_remaining <= 2:
            return "Red", days_remaining
        elif 2 < days_remaining <= 10:
            return "Yellow", days_remaining
        else:
            return "Green", days_remaining
    except:
        return "Unknown", 0

def send_email_reminders():
    """
    Simulates sending emails for deadlines.
    """
    deadlines = load_deadlines()
    emails_sent = []
    for d in deadlines:
        color, days = get_status(d["date"])
        if days == 7:
            emails_sent.append(f"Email sent (1 week remaining) for {d['source']} ({d['date']})")
        elif days == 1:
            emails_sent.append(f"Email sent (1 day remaining) for {d['source']} ({d['date']}) - URGENT!")
        elif days == 0:
            emails_sent.append(f"Email sent (DEADLINE TODAY!) for {d['source']} ({d['date']}) - FINAL NOTICE")
            
    return emails_sent
