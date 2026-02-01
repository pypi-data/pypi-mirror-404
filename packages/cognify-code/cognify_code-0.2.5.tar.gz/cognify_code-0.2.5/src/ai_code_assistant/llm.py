"""LLM Manager for multi-provider LLM integration via LangChain."""

from typing import Iterator, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from ai_code_assistant.config import Config
from ai_code_assistant.providers.base import BaseProvider, ProviderConfig, ProviderType
from ai_code_assistant.providers.factory import get_provider, get_available_providers


class LLMManager:
    """Manages LLM interactions using LangChain with multiple provider support."""

    def __init__(self, config: Config):
        """Initialize LLM manager with configuration."""
        self.config = config
        self._provider: Optional[BaseProvider] = None

    @property
    def provider(self) -> BaseProvider:
        """Get or create the provider instance."""
        if self._provider is None:
            provider_config = ProviderConfig(
                provider=ProviderType(self.config.llm.provider),
                model=self.config.llm.model,
                api_key=self.config.llm.api_key,
                base_url=self.config.llm.base_url,
                temperature=self.config.llm.temperature,
                max_tokens=self.config.llm.max_tokens,
                timeout=self.config.llm.timeout,
            )
            self._provider = get_provider(provider_config)
        return self._provider

    @property
    def llm(self) -> BaseChatModel:
        """Get the underlying LLM instance for backward compatibility."""
        return self.provider.llm

    def invoke(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Invoke the LLM with a prompt and optional system message."""
        return self.provider.invoke(prompt, system_prompt)

    def invoke_with_template(
        self,
        template: ChatPromptTemplate,
        **kwargs,
    ) -> str:
        """Invoke the LLM using a prompt template."""
        chain = template | self.llm
        response = chain.invoke(kwargs)
        return str(response.content)

    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Iterator[str]:
        """Stream LLM response for real-time output."""
        return self.provider.stream(prompt, system_prompt)

    def check_connection(self) -> bool:
        """Check if the LLM provider is accessible."""
        return self.provider.check_connection()

    def get_model_info(self) -> dict:
        """Get information about the current model configuration."""
        return self.provider.get_model_info()

    def validate_config(self) -> tuple[bool, str]:
        """Validate the current provider configuration."""
        return self.provider.validate_config()

    @staticmethod
    def list_providers() -> dict:
        """List all available providers and their models."""
        return get_available_providers()

    def switch_provider(
        self,
        provider: str,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> None:
        """
        Switch to a different provider at runtime.

        Args:
            provider: Provider name (ollama, google, groq, cerebras, openrouter, openai)
            model: Optional model name (uses provider default if not specified)
            api_key: Optional API key (uses environment variable if not specified)
        """
        provider_type = ProviderType(provider)
        
        # Get default model for provider if not specified
        if model is None:
            from ai_code_assistant.providers.factory import PROVIDER_REGISTRY
            provider_class = PROVIDER_REGISTRY.get(provider_type)
            if provider_class:
                model = provider_class.default_model
            else:
                raise ValueError(f"Unknown provider: {provider}")

        provider_config = ProviderConfig(
            provider=provider_type,
            model=model,
            api_key=api_key,
            temperature=self.config.llm.temperature,
            max_tokens=self.config.llm.max_tokens,
            timeout=self.config.llm.timeout,
        )
        self._provider = get_provider(provider_config)
