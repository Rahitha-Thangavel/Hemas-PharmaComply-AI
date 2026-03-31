import sys
import os
import shutil
import subprocess

def test_config():
    print("--- Verifying OCR Configuration ---")
    
    # 1. Check Tesseract
    tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    if os.path.exists(tesseract_path):
        print(f"✅ Tesseract found at: {tesseract_path}")
        try:
            result = subprocess.run([tesseract_path, '--version'], capture_output=True, text=True)
            print(f"   Version: {result.stdout.splitlines()[0]}")
        except Exception as e:
            print(f"❌ Tesseract found but failed to run: {e}")
    else:
        # Check system PATH
        tess_in_path = shutil.which("tesseract")
        if tess_in_path:
            print(f"✅ Tesseract found in PATH: {tess_in_path}")
        else:
            print("❌ Tesseract NOT FOUND in default path or PATH.")
    
    # 2. Check Poppler
    # (Checking for pdfinfo, which is a common poppler tool)
    poppler_in_path = shutil.which("pdfinfo")
    if poppler_in_path:
        print(f"✅ Poppler found in PATH: {poppler_in_path}")
    else:
        print("⚠️ Poppler NOT FOUND in PATH. You may need to manually add the 'bin' folder to your System PATH.")
    
    print("--- Configuration Check Complete ---")

if __name__ == "__main__":
    test_config()
