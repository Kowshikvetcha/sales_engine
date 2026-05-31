from typing import Optional
from langchain.chat_models import init_chat_model
from src.config import settings

PROVIDER_DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-6",
    "openai": "gpt-4o",
    "google": "gemini-1.5-pro",
}

def build_llm(
    model: Optional[str] = None,
    provider: Optional[str] = None,
    temperature: Optional[float] = None
):
    """
    Initializes a LangChain chat model dynamically based on parameters or config.
    Configures support for configurable fields: 'model' and 'model_provider'.
    If the selected model is not compatible with the selected provider, falls back
    to a default model for that provider.
    """
    model_provider = provider or (settings.email.provider if hasattr(settings.email, 'provider') else None) or settings.llm.default_provider
    effective_provider = model_provider.lower()
    
    model_name = model
    if not model_name:
        config_model = (settings.email.model if hasattr(settings.email, 'model') else None) or settings.llm.default_model
        
        # Check compatibility
        is_anthropic = "claude" in config_model.lower()
        is_openai = "gpt" in config_model.lower() or "o1" in config_model.lower()
        is_google = "gemini" in config_model.lower()
        
        if effective_provider == "anthropic" and is_anthropic:
            model_name = config_model
        elif effective_provider == "openai" and is_openai:
            model_name = config_model
        elif effective_provider == "google" and is_google:
            model_name = config_model
        else:
            model_name = PROVIDER_DEFAULT_MODELS.get(effective_provider, config_model)
            
    temp = temperature if temperature is not None else ((settings.email.temperature if hasattr(settings.email, 'temperature') and settings.email.temperature is not None else None) or settings.llm.temperature)
    
    return init_chat_model(
        model=model_name,
        model_provider=model_provider,
        temperature=temp,
        max_retries=3,
    )
