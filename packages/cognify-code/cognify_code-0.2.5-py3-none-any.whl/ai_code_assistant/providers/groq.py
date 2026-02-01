"""Groq provider for fast LLM inference."""

import os
from langchain_core.language_models import BaseChatModel

from ai_code_assistant.providers.base import (
    BaseProvider,
    ModelInfo,
    ProviderConfig,
    ProviderType,
)


class GroqProvider(BaseProvider):
    """Provider for Groq - extremely fast inference."""

    provider_type = ProviderType.GROQ
    display_name = "Groq (Fast Inference)"
    requires_api_key = True
    default_model = "llama-3.3-70b-versatile"
    free_tier = True

    available_models = [
        ModelInfo(
            name="llama-3.3-70b-versatile",
            provider=ProviderType.GROQ,
            description="Llama 3.3 70B - Most capable, 1000 req/day free",
            context_window=128000,
            is_free=True,
        ),
        ModelInfo(
            name="llama-3.1-8b-instant",
            provider=ProviderType.GROQ,
            description="Llama 3.1 8B - Fast, 14400 req/day free",
            context_window=128000,
            is_free=True,
        ),
        ModelInfo(
            name="llama3-70b-8192",
            provider=ProviderType.GROQ,
            description="Llama 3 70B - Powerful general model",
            context_window=8192,
            is_free=True,
        ),
        ModelInfo(
            name="mixtral-8x7b-32768",
            provider=ProviderType.GROQ,
            description="Mixtral 8x7B - Great for code",
            context_window=32768,
            is_free=True,
        ),
        ModelInfo(
            name="gemma2-9b-it",
            provider=ProviderType.GROQ,
            description="Gemma 2 9B - Google's efficient model",
            context_window=8192,
            is_free=True,
        ),
    ]

    def _create_llm(self) -> BaseChatModel:
        """Create Groq LLM instance."""
        try:
            from langchain_groq import ChatGroq
        except ImportError:
            raise ImportError(
                "langchain-groq is required for Groq provider. "
                "Install with: pip install langchain-groq"
            )

        api_key = self.config.api_key or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "Groq API key is required. Set GROQ_API_KEY environment variable "
                "or provide api_key in config. Get your key at: https://console.groq.com/keys"
            )

        return ChatGroq(
            model=self.config.model,
            api_key=api_key,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            timeout=self.config.timeout,
        )

    def validate_config(self) -> tuple[bool, str]:
        """Validate Groq configuration."""
        api_key = self.config.api_key or os.getenv("GROQ_API_KEY")
        if not api_key:
            return False, "GROQ_API_KEY environment variable or api_key config is required"
        if not self.config.model:
            return False, "Model name is required"
        return True, ""

    @classmethod
    def get_setup_instructions(cls) -> str:
        """Get Groq setup instructions."""
        return """
Groq Setup Instructions:
1. Go to https://console.groq.com/keys
2. Create a free account and generate an API key
3. Set environment variable: export GROQ_API_KEY="your-key"
4. Or add to config.yaml:
   llm:
     provider: groq
     api_key: "your-key"
     model: llama-3.3-70b-versatile

Free tier: Up to 14,400 requests/day (model dependent)
Note: Groq is EXTREMELY fast - responses in milliseconds!
"""
