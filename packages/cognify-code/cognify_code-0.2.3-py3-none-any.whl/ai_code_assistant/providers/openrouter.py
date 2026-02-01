"""OpenRouter provider for access to multiple LLM providers."""

import os
from langchain_core.language_models import BaseChatModel

from ai_code_assistant.providers.base import (
    BaseProvider,
    ModelInfo,
    ProviderConfig,
    ProviderType,
)


class OpenRouterProvider(BaseProvider):
    """Provider for OpenRouter - access to multiple LLM providers."""

    provider_type = ProviderType.OPENROUTER
    display_name = "OpenRouter (Multi-Provider)"
    requires_api_key = True
    default_model = "meta-llama/llama-3.3-70b-instruct:free"
    free_tier = True

    available_models = [
        ModelInfo(
            name="meta-llama/llama-3.3-70b-instruct:free",
            provider=ProviderType.OPENROUTER,
            description="Llama 3.3 70B - Free tier",
            context_window=128000,
            is_free=True,
        ),
        ModelInfo(
            name="google/gemma-3-27b-it:free",
            provider=ProviderType.OPENROUTER,
            description="Gemma 3 27B - Free tier",
            context_window=8192,
            is_free=True,
        ),
        ModelInfo(
            name="mistralai/mistral-small-3.1-24b-instruct:free",
            provider=ProviderType.OPENROUTER,
            description="Mistral Small 3.1 - Free tier",
            context_window=32768,
            is_free=True,
        ),
        ModelInfo(
            name="qwen/qwen3-4b:free",
            provider=ProviderType.OPENROUTER,
            description="Qwen 3 4B - Free tier, fast",
            context_window=32768,
            is_free=True,
        ),
        ModelInfo(
            name="deepseek/deepseek-r1:free",
            provider=ProviderType.OPENROUTER,
            description="DeepSeek R1 - Reasoning model, free",
            context_window=64000,
            is_free=True,
        ),
        ModelInfo(
            name="anthropic/claude-3.5-sonnet",
            provider=ProviderType.OPENROUTER,
            description="Claude 3.5 Sonnet - Paid, excellent for code",
            context_window=200000,
            is_free=False,
        ),
        ModelInfo(
            name="openai/gpt-4o",
            provider=ProviderType.OPENROUTER,
            description="GPT-4o - Paid, OpenAI's best",
            context_window=128000,
            is_free=False,
        ),
    ]

    def _create_llm(self) -> BaseChatModel:
        """Create OpenRouter LLM instance using OpenAI-compatible API."""
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError(
                "langchain-openai is required for OpenRouter provider. "
                "Install with: pip install langchain-openai"
            )

        api_key = self.config.api_key or os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenRouter API key is required. Set OPENROUTER_API_KEY environment variable "
                "or provide api_key in config. Get your key at: https://openrouter.ai/keys"
            )

        return ChatOpenAI(
            model=self.config.model,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            timeout=self.config.timeout,
            default_headers={
                "HTTP-Referer": "https://github.com/akkssy/cognify-ai",
                "X-Title": "Cognify AI",
            },
        )

    def validate_config(self) -> tuple[bool, str]:
        """Validate OpenRouter configuration."""
        api_key = self.config.api_key or os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return False, "OPENROUTER_API_KEY environment variable or api_key config is required"
        if not self.config.model:
            return False, "Model name is required"
        return True, ""

    @classmethod
    def get_setup_instructions(cls) -> str:
        """Get OpenRouter setup instructions."""
        return """
OpenRouter Setup Instructions:
1. Go to https://openrouter.ai/keys
2. Create a free account and generate an API key
3. Set environment variable: export OPENROUTER_API_KEY="your-key"
4. Or add to config.yaml:
   llm:
     provider: openrouter
     api_key: "your-key"
     model: meta-llama/llama-3.3-70b-instruct:free

Free tier: 50 requests/day on free models (models ending with :free)
Paid: Access to GPT-4, Claude, and many more models
"""
