"""LLM setup and configuration supporting multiple providers."""

from pydantic_ai.models import Model
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from urimai.config import Config


def get_model() -> Model:
    """Get configured LLM model instance based on the active provider.

    Returns:
        Model instance configured with the appropriate API key and model name

    Raises:
        RuntimeError: If the required API key is not set or provider is unknown
    """
    Config.validate()

    if Config.PROVIDER == "openai":
        from pydantic_ai.models.openai import OpenAIModel
        from pydantic_ai.providers.openai import OpenAIProvider

        provider = OpenAIProvider(api_key=Config.OPENAI_API_KEY)
        return OpenAIModel(Config.OPENAI_MODEL_NAME, provider=provider)

    # Default: Google
    provider = GoogleProvider(api_key=Config.GOOGLE_API_KEY)
    return GoogleModel(Config.MODEL_NAME, provider=provider)


def get_gemini_model() -> GoogleModel:
    """Get configured Gemini model instance.

    Deprecated: Use get_model() instead.
    """
    return get_model()
