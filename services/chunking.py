from langchain.text_splitter import RecursiveCharacterTextSplitter

def split_documents(documents, config):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config["chunking"]["chunk_size"],
        chunk_overlap=config["chunking"]["chunk_overlap"],
        separators=["\n\n", "\n", "。", "．", " ", ""],
        length_function=len,
    )
    return splitter.split_documents(documents)