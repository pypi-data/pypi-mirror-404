"""Google AI Studio (Gemini) provider."""

import os
from langchain_core.language_models import BaseChatModel

from ai_code_assistant.providers.base import (
    BaseProvider,
    ModelInfo,
    ProviderConfig,
    ProviderType,
)


class GoogleProvider(BaseProvider):
    """Provider for Google AI Studio / Gemini."""

    provider_type = ProviderType.GOOGLE
    display_name = "Google AI Studio (Gemini)"
    requires_api_key = True
    default_model = "gemini-2.0-flash"
    free_tier = True

    available_models = [
        ModelInfo(
            name="gemini-2.0-flash",
            provider=ProviderType.GOOGLE,
            description="Gemini 2.0 Flash - Fast and capable, great free tier",
            context_window=1000000,
            is_free=True,
        ),
        ModelInfo(
            name="gemini-2.0-flash-lite",
            provider=ProviderType.GOOGLE,
            description="Gemini 2.0 Flash Lite - Faster, lighter version",
            context_window=1000000,
            is_free=True,
        ),
        ModelInfo(
            name="gemini-1.5-pro",
            provider=ProviderType.GOOGLE,
            description="Gemini 1.5 Pro - Most capable Gemini model",
            context_window=2000000,
            is_free=True,
        ),
        ModelInfo(
            name="gemini-1.5-flash",
            provider=ProviderType.GOOGLE,
            description="Gemini 1.5 Flash - Fast and efficient",
            context_window=1000000,
            is_free=True,
        ),
    ]

    def _create_llm(self) -> BaseChatModel:
        """Create Google Gemini LLM instance."""
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError:
            raise ImportError(
                "langchain-google-genai is required for Google provider. "
                "Install with: pip install langchain-google-genai"
            )

        api_key = self.config.api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "Google API key is required. Set GOOGLE_API_KEY environment variable "
                "or provide api_key in config. Get your key at: https://aistudio.google.com/apikey"
            )

        return ChatGoogleGenerativeAI(
            model=self.config.model,
            google_api_key=api_key,
            temperature=self.config.temperature,
            max_output_tokens=self.config.max_tokens,
            timeout=self.config.timeout,
        )

    def validate_config(self) -> tuple[bool, str]:
        """Validate Google configuration."""
        api_key = self.config.api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return False, "GOOGLE_API_KEY environment variable or api_key config is required"
        if not self.config.model:
            return False, "Model name is required"
        return True, ""

    @classmethod
    def get_setup_instructions(cls) -> str:
        """Get Google AI Studio setup instructions."""
        return """
Google AI Studio Setup Instructions:
1. Go to https://aistudio.google.com/apikey
2. Create a new API key
3. Set environment variable: export GOOGLE_API_KEY="your-key"
4. Or add to config.yaml:
   llm:
     provider: google
     api_key: "your-key"
     model: gemini-2.0-flash

Free tier: 15 requests/minute, 1M tokens/day
"""
