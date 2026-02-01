"""
Cognify AI - Your Local AI-Powered Code Assistant.

Review, generate, search, and refactor code with an intelligent AI agent.
All running locally with complete privacy using Ollama.
"""

__version__ = "0.2.2"
__author__ = "Ashok Kumar"

from ai_code_assistant.config import Config, load_config
from ai_code_assistant.llm import LLMManager

__all__ = ["Config", "load_config", "LLMManager", "__version__"]
