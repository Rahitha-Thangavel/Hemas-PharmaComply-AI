import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

def get_llm(config):
    provider = config["llm_provider"]

    if provider == "groq":
        return ChatGroq(
            groq_api_key=os.getenv("GROQ_API_KEY"),
            model_name=config["groq"]["model"],
            temperature=config["groq"]["temperature"],
            max_tokens=config["groq"]["max_tokens"]
        )

    raise ValueError("Unsupported LLM provider")