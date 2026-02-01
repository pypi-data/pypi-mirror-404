"""Base provider class for LLM integrations."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Iterator, List, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel


class ProviderType(str, Enum):
    """Supported LLM provider types."""
    OLLAMA = "ollama"
    GOOGLE = "google"
    GROQ = "groq"
    CEREBRAS = "cerebras"
    OPENROUTER = "openrouter"
    OPENAI = "openai"


class ProviderConfig(BaseModel):
    """Configuration for an LLM provider."""
    provider: ProviderType = ProviderType.OLLAMA
    model: str = "deepseek-coder:6.7b"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 4096
    timeout: int = 120


class ModelInfo(BaseModel):
    """Information about a model."""
    name: str
    provider: ProviderType
    description: str = ""
    context_window: int = 4096
    is_free: bool = True


class BaseProvider(ABC):
    """Abstract base class for LLM providers."""

    # Provider metadata
    provider_type: ProviderType
    display_name: str
    requires_api_key: bool = True
    default_model: str
    free_tier: bool = True

    # Available models for this provider
    available_models: List[ModelInfo] = []

    def __init__(self, config: ProviderConfig):
        """Initialize the provider with configuration."""
        self.config = config
        self._llm: Optional[BaseChatModel] = None

    @property
    def llm(self) -> BaseChatModel:
        """Get or create the LLM instance."""
        if self._llm is None:
            self._llm = self._create_llm()
        return self._llm

    @abstractmethod
    def _create_llm(self) -> BaseChatModel:
        """Create the LangChain LLM instance. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def validate_config(self) -> tuple[bool, str]:
        """Validate the provider configuration. Returns (is_valid, error_message)."""
        pass

    def invoke(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Invoke the LLM with a prompt and optional system message."""
        messages: List[BaseMessage] = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        response = self.llm.invoke(messages)
        return str(response.content)

    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Iterator[str]:
        """Stream LLM response for real-time output."""
        messages: List[BaseMessage] = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        for chunk in self.llm.stream(messages):
            yield str(chunk.content)

    def check_connection(self) -> bool:
        """Check if the provider is accessible."""
        try:
            self.invoke("Say 'ok' and nothing else.")
            return True
        except Exception:
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model configuration."""
        return {
            "provider": self.provider_type.value,
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "base_url": self.config.base_url,
            "free_tier": self.free_tier,
        }

    @classmethod
    def get_available_models(cls) -> List[ModelInfo]:
        """Get list of available models for this provider."""
        return cls.available_models

    @classmethod
    def get_setup_instructions(cls) -> str:
        """Get setup instructions for this provider."""
        return f"Configure {cls.display_name} in your config.yaml or set environment variables."
