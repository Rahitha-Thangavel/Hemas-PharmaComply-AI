from langchain_community.embeddings import HuggingFaceEmbeddings

def get_embeddings(config):
    return HuggingFaceEmbeddings(
        model_name=config["embeddings"]["model"],
<<<<<<< HEAD
        model_kwargs={
            "device": "cpu",
            "trust_remote_code": True
        },
        encode_kwargs={
            "normalize_embeddings": True
        }
=======
        model_kwargs={"device": "cpu"}
>>>>>>> feature/contextual-categorization
    )