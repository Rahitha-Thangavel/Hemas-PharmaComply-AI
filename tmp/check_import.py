import sys
import os

# Ensure the root directory is in the path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

try:
    import services.change_detector as cd
    print(f"Successfully imported services.change_detector from {cd.__file__}")
    print("Available attributes in change_detector:")
    for attr in dir(cd):
        if not attr.startswith("__"):
            print(f"  - {attr}")
    
    if hasattr(cd, 'list_all_documents_in_category'):
        print("\nSUCCESS: 'list_all_documents_in_category' is present!")
    else:
        print("\nFAILURE: 'list_all_documents_in_category' is missing!")
        
except Exception as e:
    print(f"\nCRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()
