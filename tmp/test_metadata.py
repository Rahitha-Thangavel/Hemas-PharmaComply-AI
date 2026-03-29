import os
from pathlib import Path

# Mocking the Doc class as it would come from LangChain
class MockDoc:
    def __init__(self, content, metadata=None):
        self.page_content = content
        self.metadata = metadata or {}

# The logic I want to test (Standardize Metadata section from file_loader)
def standardize_metadata(docs, file_name, file_path):
    import time
    for doc in docs:
        # Standardize page indexing (PyPDFLoader is 0-indexed, OCR is 1-indexed)
        if "page" in doc.metadata:
            try:
                p_val = int(doc.metadata["page"])
                # Standard loaders are 0-indexed. OCR loader is already 1-indexed (marked by is_ocr).
                if not doc.metadata.get("is_ocr", False):
                    doc.metadata["page"] = p_val + 1
            except (ValueError, TypeError):
                doc.metadata["page"] = 1
        else:
            # Default for non-paginated docs (text, docx)
            doc.metadata["page"] = 1

        doc.metadata.update({
            "source": file_name,
            "file_path": file_path,
            "file_type": Path(file_path).suffix[1:].upper(),
            "loaded_at": time.strftime("%Y-%m-%d %H:%M:%S")
        })
    return docs

def test_metadata_standardization():
    # Test case 1: Standard PDF loader (0-indexed)
    docs_standard = [MockDoc("Page 1", {"page": 0}), MockDoc("Page 2", {"page": 1})]
    standardize_metadata(docs_standard, "test.pdf", "/path/to/test.pdf")
    
    print("Test 1 - Standard Loader (0-indexed):")
    for doc in docs_standard:
        print(f"  - Page Metadata: {doc.metadata['page']}")
    assert docs_standard[0].metadata['page'] == 1
    assert docs_standard[1].metadata['page'] == 2

    # Test case 2: OCR loader (already 1-indexed)
    docs_ocr = [MockDoc("Page 1", {"page": 1, "is_ocr": True}), MockDoc("Page 2", {"page": 2, "is_ocr": True})]
    standardize_metadata(docs_ocr, "test.pdf", "/path/to/test.pdf")
    
    print("\nTest 2 - OCR Loader (1-indexed):")
    for doc in docs_ocr:
        print(f"  - Page Metadata: {doc.metadata['page']}")
    assert docs_ocr[0].metadata['page'] == 1
    assert docs_ocr[1].metadata['page'] == 2

    # Test case 3: Text file (no page)
    docs_txt = [MockDoc("Section 1")]
    standardize_metadata(docs_txt, "test.txt", "/path/to/test.txt")
    
    print("\nTest 3 - Text File (No Page):")
    for doc in docs_txt:
        print(f"  - Page Metadata: {doc.metadata['page']}")
    assert docs_txt[0].metadata['page'] == 1

    print("\n✅ Metadata standardization tests passed!")

if __name__ == "__main__":
    test_metadata_standardization()
