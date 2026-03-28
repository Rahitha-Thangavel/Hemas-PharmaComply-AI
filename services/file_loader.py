import time
from pathlib import Path
import streamlit as st
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
    UnstructuredPDFLoader
)

def load_documents(file_paths):
    all_docs = []
    for file_path in file_paths:
        try:
            file_name = Path(file_path).name
            
            if file_path.endswith('.pdf'):
                try:
                    loader = UnstructuredPDFLoader(file_path, mode="elements")
                    docs = loader.load()
                except:
                    loader = PyPDFLoader(file_path)
                    docs = loader.load()
            
            elif file_path.endswith('.txt'):
                loader = TextLoader(file_path, encoding='utf-8')
                docs = loader.load()
            
            elif file_path.endswith(('.docx', '.doc')):
                loader = Docx2txtLoader(file_path)
                docs = loader.load()
            
            else:
                docs = []
            
            for doc in docs:
                doc.metadata.update({
                    "source": file_name,
                    "file_path": file_path,
                    "file_type": Path(file_path).suffix[1:].upper(),
                    "loaded_at": time.strftime("%Y-%m-%d %H:%M:%S")
                })
            
            all_docs.extend(docs)
                
        except Exception as e:
            st.warning(f"⚠️ Failed to load {file_path}: {e}")
            
    return all_docs