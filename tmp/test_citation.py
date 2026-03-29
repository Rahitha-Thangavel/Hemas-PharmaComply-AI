import os
import sys
from pathlib import Path

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Mocking parts of langchain/streamit if needed or just testing the logic
class MockDoc:
    def __init__(self, content, source, page):
        self.page_content = content
        self.metadata = {'source': source, 'page': page, 'file_path': f'/path/to/{source}'}

def test_filtering():
    from app.core.chatbot import HemasPharmaComplyAI
    
    # We dont need a real chatbot instance, we just want to test _extract_sources logic
    # But _extract_sources is a method, so we need an instance or mock it.
    
    class Tester(HemasPharmaComplyAI):
        def __init__(self):
            pass # Skip real init
            
    tester = Tester()
    
    # Case 1: Answer cites specific page
    result = {
        'answer': "The cold chain equipment includes refrigerators and cold boxes (Source: Guidelines.pdf, Page 2).",
        'source_documents': [
            MockDoc("Refrigerators are key...", "Guidelines.pdf", 2),
            MockDoc("Other irrelevant info...", "Guidelines.pdf", 5),
            MockDoc("Some other doc...", "Rules.pdf", 1)
        ]
    }
    
    sources = tester._extract_sources(result)
    print(f"Test 1 - Explicit citation: Found {len(sources)} sources")
    for s in sources:
        print(f"  - {s['document']} Page {s['page']}")
        
    # Case 2: Answer mentions doc but no page
    result2 = {
        'answer': " NMRA regulates pricing for all medicines as per the Guidelines.",
        'source_documents': [
            MockDoc("Section 1: Pricing...", "Guidelines.pdf", 1),
            MockDoc("Section 10: Misc...", "Guidelines.pdf", 10)
        ]
    }
    sources2 = tester._extract_sources(result2)
    print(f"\nTest 2 - Doc mention only: Found {len(sources2)} sources")
    for s in sources2:
         print(f"  - {s['document']} Page {s['page']}")

    # Case 3: No mention at all (fallback to top 1)
    result3 = {
        'answer': "The regulation says X.",
        'source_documents': [
            MockDoc("Chunk 1 content", "Doc1.pdf", 1),
            MockDoc("Chunk 2 content", "Doc2.pdf", 2)
        ]
    }
    sources3 = tester._extract_sources(result3)
    print(f"\nTest 3 - No mention (fallback): Found {len(sources3)} sources")
    for s in sources3:
         print(f"  - {s['document']} Page {s['page']}")

if __name__ == "__main__":
    test_filtering()
