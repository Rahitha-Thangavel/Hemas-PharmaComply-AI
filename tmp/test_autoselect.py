import sys
import os

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from services.change_detector import find_previous_document

def test_autoselect():
    print("--- Testing Smart Auto-select Logic ---")
    
    categories = [
        "Price Control", 
        "Registration & Fees", 
        "Labelling & Requirements", 
        "Other Regulations"
    ]
    
    for cat in categories:
        path = find_previous_document(cat)
        if path:
            print(f"✅ Category: {cat}")
            print(f"   Found: {os.path.basename(path)}")
        else:
            print(f"❌ Category: {cat}")
            print(f"   Result: Not found in database.")
    
    print("--- Test Complete ---")

if __name__ == "__main__":
    test_autoselect()
