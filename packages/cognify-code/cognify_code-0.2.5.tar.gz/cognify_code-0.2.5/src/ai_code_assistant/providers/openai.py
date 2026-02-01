"""OpenAI provider for GPT models."""

import os
from langchain_core.language_models import BaseChatModel

from ai_code_assistant.providers.base import (
    BaseProvider,
    ModelInfo,
    ProviderConfig,
    ProviderType,
)


class OpenAIProvider(BaseProvider):
    """Provider for OpenAI GPT models."""

    provider_type = ProviderType.OPENAI
    display_name = "OpenAI"
    requires_api_key = True
    default_model = "gpt-4o-mini"
    free_tier = False

    available_models = [
        ModelInfo(
            name="gpt-4o-mini",
            provider=ProviderType.OPENAI,
            description="GPT-4o Mini - Fast and affordable",
            context_window=128000,
            is_free=False,
        ),
        ModelInfo(
            name="gpt-4o",
            provider=ProviderType.OPENAI,
            description="GPT-4o - Most capable",
            context_window=128000,
            is_free=False,
        ),
        ModelInfo(
            name="gpt-4-turbo",
            provider=ProviderType.OPENAI,
            description="GPT-4 Turbo - Fast GPT-4",
            context_window=128000,
            is_free=False,
        ),
        ModelInfo(
            name="gpt-3.5-turbo",
            provider=ProviderType.OPENAI,
            description="GPT-3.5 Turbo - Fast and cheap",
            context_window=16385,
            is_free=False,
        ),
        ModelInfo(
            name="o1-mini",
            provider=ProviderType.OPENAI,
            description="o1-mini - Reasoning model",
            context_window=128000,
            is_free=False,
        ),
    ]

    def _create_llm(self) -> BaseChatModel:
        """Create OpenAI LLM instance."""
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError(
                "langchain-openai is required for OpenAI provider. "
                "Install with: pip install langchain-openai"
            )

        api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable "
                "or provide api_key in config. Get your key at: https://platform.openai.com/api-keys"
            )

        return ChatOpenAI(
            model=self.config.model,
            api_key=api_key,
            base_url=self.config.base_url,  # Allow custom base URL for Azure, etc.
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            timeout=self.config.timeout,
        )

    def validate_config(self) -> tuple[bool, str]:
        """Validate OpenAI configuration."""
        api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            return False, "OPENAI_API_KEY environment variable or api_key config is required"
        if not self.config.model:
            return False, "Model name is required"
        return True, ""

    @classmethod
    def get_setup_instructions(cls) -> str:
        """Get OpenAI setup instructions."""
        return """
OpenAI Setup Instructions:
1. Go to https://platform.openai.com/api-keys
2. Create an API key (requires payment method)
3. Set environment variable: export OPENAI_API_KEY="your-key"
4. Or add to config.yaml:
   llm:
     provider: openai
     api_key: "your-key"
     model: gpt-4o-mini

Note: OpenAI requires a paid account. Consider using free alternatives:
- Groq (free tier with Llama models)
- Google AI Studio (free tier with Gemini)
- OpenRouter (free tier with various models)
"""
