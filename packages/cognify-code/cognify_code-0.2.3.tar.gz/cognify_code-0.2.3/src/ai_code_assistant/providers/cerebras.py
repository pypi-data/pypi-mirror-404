"""Cerebras provider for fast LLM inference."""

import os
from langchain_core.language_models import BaseChatModel

from ai_code_assistant.providers.base import (
    BaseProvider,
    ModelInfo,
    ProviderConfig,
    ProviderType,
)


class CerebrasProvider(BaseProvider):
    """Provider for Cerebras - fast inference with large models."""

    provider_type = ProviderType.CEREBRAS
    display_name = "Cerebras (Fast Inference)"
    requires_api_key = True
    default_model = "llama3.1-8b"
    free_tier = True

    available_models = [
        ModelInfo(
            name="llama3.1-8b",
            provider=ProviderType.CEREBRAS,
            description="Llama 3.1 8B - Fast and efficient",
            context_window=8192,
            is_free=True,
        ),
        ModelInfo(
            name="llama3.1-70b",
            provider=ProviderType.CEREBRAS,
            description="Llama 3.1 70B - More capable",
            context_window=8192,
            is_free=True,
        ),
        ModelInfo(
            name="llama-3.3-70b",
            provider=ProviderType.CEREBRAS,
            description="Llama 3.3 70B - Latest Llama model",
            context_window=8192,
            is_free=True,
        ),
    ]

    def _create_llm(self) -> BaseChatModel:
        """Create Cerebras LLM instance using OpenAI-compatible API."""
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError(
                "langchain-openai is required for Cerebras provider. "
                "Install with: pip install langchain-openai"
            )

        api_key = self.config.api_key or os.getenv("CEREBRAS_API_KEY")
        if not api_key:
            raise ValueError(
                "Cerebras API key is required. Set CEREBRAS_API_KEY environment variable "
                "or provide api_key in config. Get your key at: https://cloud.cerebras.ai/"
            )

        return ChatOpenAI(
            model=self.config.model,
            api_key=api_key,
            base_url="https://api.cerebras.ai/v1",
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            timeout=self.config.timeout,
        )

    def validate_config(self) -> tuple[bool, str]:
        """Validate Cerebras configuration."""
        api_key = self.config.api_key or os.getenv("CEREBRAS_API_KEY")
        if not api_key:
            return False, "CEREBRAS_API_KEY environment variable or api_key config is required"
        if not self.config.model:
            return False, "Model name is required"
        return True, ""

    @classmethod
    def get_setup_instructions(cls) -> str:
        """Get Cerebras setup instructions."""
        return """
Cerebras Setup Instructions:
1. Go to https://cloud.cerebras.ai/
2. Create a free account and generate an API key
3. Set environment variable: export CEREBRAS_API_KEY="your-key"
4. Or add to config.yaml:
   llm:
     provider: cerebras
     api_key: "your-key"
     model: llama3.1-8b

Free tier: 14,400 requests/day, very fast inference
"""
