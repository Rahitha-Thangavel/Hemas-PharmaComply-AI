import os
from pathlib import Path

# Mocking the Doc class as it would come from LangChain
class MockDoc:
    def __init__(self, content, source, page):
        self.page_content = content
        self.metadata = {'source': source, 'page': page, 'file_path': f'/path/to/{source}'}

# The logic I want to test
def _extract_sources(result):
    answer = result.get('answer', '')
    source_docs = result.get('source_documents', [])
    sources = []
    seen = set()

    # First pass: Look for explicit citations matching (Document, Page)
    for doc in source_docs:
        doc_name = doc.metadata.get('source', 'Unknown')
        page = str(doc.metadata.get('page', ''))
        doc_stem = Path(doc_name).stem.lower()
        
        # Check if both doc name and page are in the answer
        citation_present = (doc_stem in answer.lower()) and (f"page {page}" in answer.lower() or f"p.{page}" in answer.lower() or f"p {page}" in answer.lower())
        
        if citation_present:
            excerpt = doc.page_content[:400].replace('\n', ' ').strip()
            key = (doc_name, page, excerpt[:100])
            if key not in seen:
                seen.add(key)
                sources.append({
                    "document": doc_name,
                    "file_path": doc.metadata.get('file_path', ''),
                    "page": page,
                    "excerpt": f"{excerpt}..." if excerpt else "No excerpt available."
                })

    # Second pass fallback: If no explicit citations matched, but the answer mentions the doc name
    if not sources:
        for doc in source_docs:
            doc_name = doc.metadata.get('source', 'Unknown')
            doc_stem = Path(doc_name).stem.lower()
            
            if doc_stem in answer.lower():
                page = str(doc.metadata.get('page', 'N/A'))
                excerpt = doc.page_content[:400].replace('\n', ' ').strip()
                key = (doc_name, page, excerpt[:100])
                if key not in seen:
                    seen.add(key)
                    sources.append({
                        "document": doc_name,
                        "file_path": doc.metadata.get('file_path', ''),
                        "page": page,
                        "excerpt": f"{excerpt}..."
                    })

    # Final fallback: If still nothing
    if not sources and source_docs and "i cannot find" not in answer.lower():
        doc = source_docs[0]
        sources.append({
            "document": doc.metadata.get('source', 'Unknown'),
            "file_path": doc.metadata.get('file_path', ''),
            "page": doc.metadata.get('page', 'N/A'),
            "excerpt": doc.page_content[:400].replace('\n', ' ').strip() + "..."
        })

    return sources

def test_filtering():
    # Case 1: Answer cites specific page
    result = {
        'answer': "The cold chain equipment includes refrigerators and cold boxes (Source: Guidelines.pdf, Page 2).",
        'source_documents': [
            MockDoc("Refrigerators are key...", "Guidelines.pdf", 2),
            MockDoc("Other irrelevant info...", "Guidelines.pdf", 5),
            MockDoc("Some other doc...", "Rules.pdf", 1)
        ]
    }
    
    sources = _extract_sources(result)
    print(f"Test 1 - Explicit citation: Found {len(sources)} sources")
    for s in sources:
        print(f"  - {s['document']} Page {s['page']}")
    assert len(sources) == 1
    assert sources[0]['page'] == "2"
        
    # Case 2: Answer mentions doc but no page
    result2 = {
        'answer': "NMRA regulates pricing for all medicines as per the Guidelines.",
        'source_documents': [
            MockDoc("Section 1: Pricing...", "Guidelines.pdf", 1),
            MockDoc("Section 10: Misc...", "Guidelines.pdf", 10)
        ]
    }
    sources2 = _extract_sources(result2)
    print(f"\nTest 2 - Doc mention only: Found {len(sources2)} sources")
    for s in sources2:
         print(f"  - {s['document']} Page {s['page']}")
    assert len(sources2) == 2 # Should return all from that doc since page wasn't specified

    # Case 3: No mention at all (fallback to top 1)
    result3 = {
        'answer': "The regulation says X.",
        'source_documents': [
            MockDoc("Chunk 1 content", "Doc1.pdf", 1),
            MockDoc("Chunk 2 content", "Doc2.pdf", 2)
        ]
    }
    sources3 = _extract_sources(result3)
    print(f"\nTest 3 - No mention (fallback): Found {len(sources3)} sources")
    for s in sources3:
         print(f"  - {s['document']} Page {s['page']}")
    assert len(sources3) == 1 # Fallback to top result

    print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_filtering()
