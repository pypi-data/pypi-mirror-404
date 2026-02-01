"""Git integration module for AI Code Assistant."""

from ai_code_assistant.git.manager import GitManager
from ai_code_assistant.git.commit_generator import CommitMessageGenerator

__all__ = ["GitManager", "CommitMessageGenerator"]
