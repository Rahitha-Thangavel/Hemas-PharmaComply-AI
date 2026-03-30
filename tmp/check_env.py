import sys
import os
import subprocess

print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"sys.path: {sys.path}")

try:
    import streamlit
    print(f"Streamlit version: {streamlit.__version__}")
    print(f"Streamlit path: {streamlit.__file__}")
except ImportError as e:
    print(f"Streamlit import failed: {e}")

try:
    import langchain
    print(f"LangChain imported successfully")
except ImportError as e:
    print(f"LangChain import failed: {e}")
