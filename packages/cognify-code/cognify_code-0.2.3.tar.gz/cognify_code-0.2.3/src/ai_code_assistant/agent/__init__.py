"""AI Code Agent - Intelligent code generation, review, and editing."""

from ai_code_assistant.agent.file_manager import (
    FileContextManager,
    FileInfo,
    ProjectContext,
)
from ai_code_assistant.agent.intent_classifier import (
    IntentClassifier,
    Intent,
    IntentType,
)
from ai_code_assistant.agent.code_generator import (
    CodeGenerator,
    CodeGenerationRequest,
    GeneratedCode,
)
from ai_code_assistant.agent.diff_engine import (
    DiffEngine,
    ChangeSet,
    FileDiff,
    ChangeType,
)
from ai_code_assistant.agent.code_reviewer import (
    CodeReviewer,
    CodeIssue,
    ReviewResult,
    IssueSeverity,
    IssueCategory,
)
from ai_code_assistant.agent.code_agent import (
    CodeAgent,
    AgentResponse,
)

__all__ = [
    # File Manager
    "FileContextManager",
    "FileInfo",
    "ProjectContext",
    # Intent Classifier
    "IntentClassifier",
    "Intent",
    "IntentType",
    # Code Generator
    "CodeGenerator",
    "CodeGenerationRequest",
    "GeneratedCode",
    # Diff Engine
    "DiffEngine",
    "ChangeSet",
    "FileDiff",
    "ChangeType",
    # Code Reviewer
    "CodeReviewer",
    "CodeIssue",
    "ReviewResult",
    "IssueSeverity",
    "IssueCategory",
    # Code Agent
    "CodeAgent",
    "AgentResponse",
]
