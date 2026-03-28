from langchain_community.embeddings import HuggingFaceEmbeddings

def get_embeddings(config):
    return HuggingFaceEmbeddings(
        model_name=config["embeddings"]["model"],
        model_kwargs={"device": "cpu"}
    )