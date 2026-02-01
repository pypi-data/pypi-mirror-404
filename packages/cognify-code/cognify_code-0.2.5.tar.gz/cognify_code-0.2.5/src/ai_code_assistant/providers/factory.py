"""Factory for creating LLM providers."""

from typing import Dict, List, Optional, Type

from ai_code_assistant.providers.base import (
    BaseProvider,
    ModelInfo,
    ProviderConfig,
    ProviderType,
)
from ai_code_assistant.providers.ollama import OllamaProvider
from ai_code_assistant.providers.google import GoogleProvider
from ai_code_assistant.providers.groq import GroqProvider
from ai_code_assistant.providers.cerebras import CerebrasProvider
from ai_code_assistant.providers.openrouter import OpenRouterProvider
from ai_code_assistant.providers.openai import OpenAIProvider


# Registry of all available providers
PROVIDER_REGISTRY: Dict[ProviderType, Type[BaseProvider]] = {
    ProviderType.OLLAMA: OllamaProvider,
    ProviderType.GOOGLE: GoogleProvider,
    ProviderType.GROQ: GroqProvider,
    ProviderType.CEREBRAS: CerebrasProvider,
    ProviderType.OPENROUTER: OpenRouterProvider,
    ProviderType.OPENAI: OpenAIProvider,
}


def get_provider(config: ProviderConfig) -> BaseProvider:
    """
    Create a provider instance based on configuration.

    Args:
        config: Provider configuration

    Returns:
        Configured provider instance

    Raises:
        ValueError: If provider type is not supported
    """
    provider_class = PROVIDER_REGISTRY.get(config.provider)
    if not provider_class:
        supported = ", ".join(p.value for p in ProviderType)
        raise ValueError(
            f"Unsupported provider: {config.provider}. "
            f"Supported providers: {supported}"
        )

    return provider_class(config)


def get_available_providers() -> Dict[str, Dict]:
    """
    Get information about all available providers.

    Returns:
        Dictionary with provider info including name, models, and setup instructions
    """
    providers = {}
    for provider_type, provider_class in PROVIDER_REGISTRY.items():
        providers[provider_type.value] = {
            "display_name": provider_class.display_name,
            "requires_api_key": provider_class.requires_api_key,
            "free_tier": provider_class.free_tier,
            "default_model": provider_class.default_model,
            "models": [m.model_dump() for m in provider_class.available_models],
            "setup_instructions": provider_class.get_setup_instructions(),
        }
    return providers


def get_all_models() -> List[ModelInfo]:
    """
    Get all available models across all providers.

    Returns:
        List of all available models
    """
    models = []
    for provider_class in PROVIDER_REGISTRY.values():
        models.extend(provider_class.available_models)
    return models


def get_free_models() -> List[ModelInfo]:
    """
    Get all free models across all providers.

    Returns:
        List of free models
    """
    return [m for m in get_all_models() if m.is_free]


def get_provider_for_model(model_name: str) -> Optional[ProviderType]:
    """
    Find which provider a model belongs to.

    Args:
        model_name: Name of the model

    Returns:
        Provider type or None if not found
    """
    for provider_class in PROVIDER_REGISTRY.values():
        for model in provider_class.available_models:
            if model.name == model_name:
                return provider_class.provider_type
    return None


def create_provider_from_env() -> BaseProvider:
    """
    Create a provider based on available environment variables.

    Checks for API keys in order of preference and creates the appropriate provider.

    Returns:
        Configured provider instance
    """
    import os

    # Check providers in order of preference (free tiers first)
    env_checks = [
        ("GROQ_API_KEY", ProviderType.GROQ, GroqProvider.default_model),
        ("GOOGLE_API_KEY", ProviderType.GOOGLE, GoogleProvider.default_model),
        ("CEREBRAS_API_KEY", ProviderType.CEREBRAS, CerebrasProvider.default_model),
        ("OPENROUTER_API_KEY", ProviderType.OPENROUTER, OpenRouterProvider.default_model),
        ("OPENAI_API_KEY", ProviderType.OPENAI, OpenAIProvider.default_model),
    ]

    for env_var, provider_type, default_model in env_checks:
        if os.getenv(env_var):
            config = ProviderConfig(
                provider=provider_type,
                model=default_model,
                api_key=os.getenv(env_var),
            )
            return get_provider(config)

    # Default to Ollama (no API key required)
    config = ProviderConfig(
        provider=ProviderType.OLLAMA,
        model=OllamaProvider.default_model,
    )
    return get_provider(config)
