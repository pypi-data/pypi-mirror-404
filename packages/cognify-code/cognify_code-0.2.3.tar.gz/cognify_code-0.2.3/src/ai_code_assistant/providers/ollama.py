"""Ollama provider for local LLM inference."""

from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama

from ai_code_assistant.providers.base import (
    BaseProvider,
    ModelInfo,
    ProviderConfig,
    ProviderType,
)


class OllamaProvider(BaseProvider):
    """Provider for Ollama local LLM inference."""

    provider_type = ProviderType.OLLAMA
    display_name = "Ollama (Local)"
    requires_api_key = False
    default_model = "deepseek-coder:6.7b"
    free_tier = True

    available_models = [
        ModelInfo(
            name="deepseek-coder:6.7b",
            provider=ProviderType.OLLAMA,
            description="DeepSeek Coder 6.7B - Great for code tasks",
            context_window=16384,
            is_free=True,
        ),
        ModelInfo(
            name="codellama:7b",
            provider=ProviderType.OLLAMA,
            description="Code Llama 7B - Meta's code model",
            context_window=16384,
            is_free=True,
        ),
        ModelInfo(
            name="llama3.1:8b",
            provider=ProviderType.OLLAMA,
            description="Llama 3.1 8B - General purpose",
            context_window=128000,
            is_free=True,
        ),
        ModelInfo(
            name="qwen2.5-coder:7b",
            provider=ProviderType.OLLAMA,
            description="Qwen 2.5 Coder 7B - Excellent for code",
            context_window=32768,
            is_free=True,
        ),
        ModelInfo(
            name="mistral:7b",
            provider=ProviderType.OLLAMA,
            description="Mistral 7B - Fast and capable",
            context_window=32768,
            is_free=True,
        ),
    ]

    def _create_llm(self) -> BaseChatModel:
        """Create Ollama LLM instance."""
        return ChatOllama(
            model=self.config.model,
            base_url=self.config.base_url or "http://localhost:11434",
            temperature=self.config.temperature,
            num_predict=self.config.max_tokens,
            timeout=self.config.timeout,
        )

    def validate_config(self) -> tuple[bool, str]:
        """Validate Ollama configuration."""
        if not self.config.model:
            return False, "Model name is required"
        return True, ""

    @classmethod
    def get_setup_instructions(cls) -> str:
        """Get Ollama setup instructions."""
        return """
Ollama Setup Instructions:
1. Install Ollama: https://ollama.ai
2. Pull a model: ollama pull deepseek-coder:6.7b
3. Start Ollama: ollama serve
4. No API key required - runs completely locally!
"""
