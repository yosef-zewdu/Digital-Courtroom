import os
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from dotenv import load_dotenv

load_dotenv()

def get_llm(provider: Optional[str] = None, model: Optional[str] = None) -> BaseChatModel:
    """
    Returns a LangChain ChatModel instance based on the provider.
    Supported providers: 'gemini', 'openrouter'.
    """
    provider = provider or os.getenv("LLM_PROVIDER", "gemini").lower()
    
    if provider == "gemini":
        model = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        return ChatGoogleGenerativeAI(model=model, temperature=0)
    
    elif provider == "openrouter":
        model = model or os.getenv("OPENROUTER_MODEL", "arcee-ai/trinity-large-preview:free")
        api_key = os.getenv("OPENROUTER_API_KEY")
        return ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            openai_api_key=api_key,
            model=model,
            temperature=0
        )
    
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
