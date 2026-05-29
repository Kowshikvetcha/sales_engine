from typing import Optional
from langchain.chat_models import init_chat_model
from src.config import settings

def build_llm(
    model: Optional[str] = None,
    provider: Optional[str] = None,
    temperature: Optional[float] = None
):
    """
    Initializes a LangChain chat model dynamically based on parameters or config.
    Configures support for configurable fields: 'model' and 'model_provider'.
    """
    model_name = model or settings.llm.default_model
    model_provider = provider or settings.llm.default_provider
    temp = temperature if temperature is not None else settings.llm.temperature
    
    return init_chat_model(
        model=model_name,
        model_provider=model_provider,
        temperature=temp,
        max_retries=3,
    )
