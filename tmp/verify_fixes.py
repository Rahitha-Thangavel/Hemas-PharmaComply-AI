import os
import sys

# Add root to path
sys.path.append(os.getcwd())

from services.file_loader import load_documents
from services.metadata_manager import find_files_by_category, load_metadata

# Target files in data/raw
raw_dir = "data/raw"
files = [
    os.path.join(raw_dir, "2019 price list text.pdf"),
    os.path.join(raw_dir, "Maximum Retail Prices of Medicines 2021.pdf"),
    os.path.join(raw_dir, "New-Maximum-Prices-of-Essential-Medicines-2025-November-NMRA.pdf")
]

print("--- Categorizing Files via AI Context ---")
# load_documents will trigger classify_document_by_context
docs = load_documents(files)

print("\n--- Metadata Cache ---")
meta = load_metadata()
for f, data in meta.items():
    print(f"{f}: Category={data.get('category')}, Year={data.get('year')}")

print("\n--- Testing find_previous_document('Price Control') ---")
matches = find_files_by_category("Price Control", raw_dir)
for i, m in enumerate(matches):
    print(f"{i+1}. {os.path.basename(m[0])} (Year: {m[1]})")
