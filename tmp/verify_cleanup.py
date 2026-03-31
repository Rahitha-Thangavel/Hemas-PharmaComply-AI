import os
import sys
from pathlib import Path

# Add project root to sys.path
project_root = r"c:\Rahitha Folder\Hemas AITHON 2026\Hemas PharmaComply AI"
sys.path.insert(0, project_root)

from app.features.deadline.deadline_service import validate_db, load_deadlines

data_raw = os.path.join(project_root, "data", "raw")
print(f"Cleaning up DB using source dir: {data_raw}")

removed = validate_db(data_raw)
print(f"Removed {removed} obsolete entries.")

deadlines = load_deadlines()
print(f"Remaining deadlines: {len(deadlines)}")
for d in deadlines:
    print(f"- {d['source']} ({d['date']})")
