import os
<<<<<<< HEAD
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()
=======
from pathlib import Path
from langchain_groq import ChatGroq
from dotenv import load_dotenv

# Load .env from the root directory (two levels up from this file: app/core/llm_factory.py)
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    # Fallback to current working directory
    load_dotenv()
>>>>>>> feature/contextual-categorization

def get_llm(config):
    provider = config["llm_provider"]

    if provider == "groq":
<<<<<<< HEAD
        return ChatGroq(
            groq_api_key=os.getenv("GROQ_API_KEY"),
=======
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            error_msg = f"❌ GROQ_API_KEY not found! \nChecked path: {env_path}\nFile exists: {env_path.exists()}"
            raise ValueError(error_msg)
        return ChatGroq(
            groq_api_key=api_key,
>>>>>>> feature/contextual-categorization
            model_name=config["groq"]["model"],
            temperature=config["groq"]["temperature"],
            max_tokens=config["groq"]["max_tokens"]
        )

    raise ValueError("Unsupported LLM provider")