"""Intent Classifier for understanding user requests."""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple


class IntentType(Enum):
    """Types of user intents."""
    CODE_GENERATE = "code_generate"      # Create new code
    CODE_EDIT = "code_edit"              # Modify existing code
    CODE_REVIEW = "code_review"          # Review code for issues
    CODE_EXPLAIN = "code_explain"        # Explain how code works
    CODE_REFACTOR = "code_refactor"      # Refactor/improve code
    TEST_GENERATE = "test_generate"      # Generate tests
    FILE_CREATE = "file_create"          # Create a new file
    FILE_DELETE = "file_delete"          # Delete a file
    PROJECT_INFO = "project_info"        # Get project information
    GENERAL_CHAT = "general_chat"        # General conversation


@dataclass
class Intent:
    """Represents a classified intent."""
    type: IntentType
    confidence: float
    file_paths: List[str] = field(default_factory=list)
    target_description: str = ""
    action_description: str = ""
    language: Optional[str] = None
    
    @property
    def requires_file_context(self) -> bool:
        """Check if this intent needs file context."""
        return self.type in {
            IntentType.CODE_EDIT,
            IntentType.CODE_REVIEW,
            IntentType.CODE_EXPLAIN,
            IntentType.CODE_REFACTOR,
            IntentType.TEST_GENERATE,
        }
    
    @property
    def modifies_files(self) -> bool:
        """Check if this intent will modify files."""
        return self.type in {
            IntentType.CODE_GENERATE,
            IntentType.CODE_EDIT,
            IntentType.CODE_REFACTOR,
            IntentType.TEST_GENERATE,
            IntentType.FILE_CREATE,
            IntentType.FILE_DELETE,
        }


# Keyword patterns for intent detection
INTENT_PATTERNS = {
    IntentType.CODE_GENERATE: [
        r"\b(create|write|generate|make|build|implement|add)\b.*\b(function|class|method|api|endpoint|component|module|service)\b",
        r"\b(create|write|generate|make|build)\b.*\b(code|script|program)\b",
        r"\bnew\b.*\b(function|class|file|component)\b",
        r"\bimplement\b",
    ],
    IntentType.CODE_EDIT: [
        r"\b(edit|modify|change|update|fix|patch)\b.*\b(code|file|function|class|line)\b",
        r"\b(add|insert|append)\b.*\b(to|in|into)\b",
        r"\b(remove|delete)\b.*\b(from|in)\b.*\b(code|file|function)\b",
        r"\bfix\b.*\b(bug|error|issue|problem)\b",
        r"\bchange\b.*\bto\b",
    ],
    IntentType.CODE_REVIEW: [
        r"\b(review|check|analyze|audit|inspect)\b",
        r"\b(find|look for|check for)\b.*\b(issues|bugs|problems|errors|vulnerabilities)\b",
        r"\b(security|performance)\b.*\b(review|check|audit)\b",
        r"\bcode\s*review\b",
        r"\breview\b.*\.(py|js|ts|java|go|rs|rb|cpp|c)\b",
    ],
    IntentType.CODE_EXPLAIN: [
        r"\b(explain|describe)\b",
        r"\b(what does|how does|what is|how is)\b.*\b(code|function|class|file|this|it|work)\b",
        r"\bwalk\s*(me\s*)?through\b",
        r"\bunderstand\b.*\b(code|function|class)\b",
        r"\bwhat\b.*\b(doing|happening|mean)\b",
        r"\bexplain\b.*\.(py|js|ts|java|go|rs|rb|cpp|c)\b",
    ],
    IntentType.CODE_REFACTOR: [
        r"\b(refactor|improve|optimize|clean|simplify|restructure)\b",
        r"\bmake\b.*\b(better|cleaner|faster|more efficient|readable)\b",
        r"\b(reduce|remove)\b.*\b(duplication|complexity)\b",
    ],
    IntentType.TEST_GENERATE: [
        r"\b(create|write|generate|add)\b.*\b(test|tests|unit test|spec)\b",
        r"\btest\b.*\b(for|coverage)\b",
        r"\b(pytest|unittest|jest|mocha)\b",
    ],
    IntentType.FILE_CREATE: [
        r"\b(create|make|new)\b.*\b(file|directory|folder)\b",
        r"\btouch\b",
    ],
    IntentType.FILE_DELETE: [
        r"\b(delete|remove|rm)\b.*\b(file|directory|folder)\b",
    ],
    IntentType.PROJECT_INFO: [
        r"\b(show|list|what)\b.*\b(files|structure|project)\b",
        r"\bproject\b.*\b(structure|info|overview)\b",
        r"\bwhat\s*(files|languages)\b",
    ],
}

# File path patterns
FILE_PATH_PATTERNS = [
    r'["\']([^"\']+\.[a-zA-Z]{1,10})["\']',  # Quoted paths with extension
    r'\b(\S+\.(?:py|js|ts|jsx|tsx|java|go|rs|c|cpp|h|rb|php|swift|kt|scala|sql|yaml|yml|json|toml|xml|html|css|md))\b',  # Unquoted paths
    r'\b(src/\S+)\b',  # src/ paths
    r'\b(tests?/\S+)\b',  # test/ paths
    r'\b(lib/\S+)\b',  # lib/ paths
    r'\b(app/\S+)\b',  # app/ paths
]

# Language detection patterns
LANGUAGE_PATTERNS = {
    "python": [r"\bpython\b", r"\bpy\b", r"\.py\b", r"\bdjango\b", r"\bflask\b", r"\bfastapi\b"],
    "javascript": [r"\bjavascript\b", r"\bjs\b", r"\.js\b", r"\bnode\b", r"\breact\b", r"\bvue\b"],
    "typescript": [r"\btypescript\b", r"\bts\b", r"\.ts\b", r"\.tsx\b"],
    "java": [r"\bjava\b", r"\.java\b", r"\bspring\b"],
    "go": [r"\bgo\b", r"\bgolang\b", r"\.go\b"],
    "rust": [r"\brust\b", r"\.rs\b", r"\bcargo\b"],
    "ruby": [r"\bruby\b", r"\.rb\b", r"\brails\b"],
    "php": [r"\bphp\b", r"\.php\b", r"\blaravel\b"],
}


class IntentClassifier:
    """Classifies user messages into intents."""
    
    def __init__(self, llm_manager=None):
        self.llm = llm_manager
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for efficiency."""
        self._intent_patterns = {
            intent: [re.compile(p, re.IGNORECASE) for p in patterns]
            for intent, patterns in INTENT_PATTERNS.items()
        }
        self._file_patterns = [re.compile(p) for p in FILE_PATH_PATTERNS]
        self._language_patterns = {
            lang: [re.compile(p, re.IGNORECASE) for p in patterns]
            for lang, patterns in LANGUAGE_PATTERNS.items()
        }
    
    def classify(self, message: str) -> Intent:
        """Classify a user message into an intent."""
        # Extract file paths
        file_paths = self._extract_file_paths(message)
        
        # Detect language
        language = self._detect_language(message)
        
        # Score each intent type
        scores: List[Tuple[IntentType, float]] = []
        
        for intent_type, patterns in self._intent_patterns.items():
            score = 0.0
            for pattern in patterns:
                if pattern.search(message):
                    score += 1.0
            
            if score > 0:
                # Normalize by number of patterns
                score = score / len(patterns)
                scores.append((intent_type, score))
        
        # Sort by score
        scores.sort(key=lambda x: x[1], reverse=True)
        
        if scores:
            best_intent, confidence = scores[0]
        else:
            best_intent = IntentType.GENERAL_CHAT
            confidence = 0.5
        
        # Boost confidence if file paths found for file-related intents
        if file_paths and best_intent.value.startswith("code_"):
            confidence = min(confidence + 0.2, 1.0)
        
        return Intent(
            type=best_intent,
            confidence=confidence,
            file_paths=file_paths,
            target_description=self._extract_target(message, best_intent),
            action_description=message,
            language=language,
        )
    
    def classify_with_llm(self, message: str) -> Intent:
        """Use LLM for more accurate classification."""
        if not self.llm:
            return self.classify(message)
        
        # First do rule-based classification
        rule_intent = self.classify(message)
        
        # Use LLM to refine
        prompt = f"""Classify this user request into one of these categories:
- code_generate: Create new code (function, class, API, etc.)
- code_edit: Modify existing code
- code_review: Review code for issues/bugs
- code_explain: Explain how code works
- code_refactor: Improve/optimize code
- test_generate: Create tests
- file_create: Create new file
- file_delete: Delete file
- project_info: Get project information
- general_chat: General conversation

User request: "{message}"

Respond with ONLY the category name, nothing else."""

        try:
            response = self.llm.invoke(prompt).strip().lower()
            
            # Map response to IntentType
            intent_map = {
                "code_generate": IntentType.CODE_GENERATE,
                "code_edit": IntentType.CODE_EDIT,
                "code_review": IntentType.CODE_REVIEW,
                "code_explain": IntentType.CODE_EXPLAIN,
                "code_refactor": IntentType.CODE_REFACTOR,
                "test_generate": IntentType.TEST_GENERATE,
                "file_create": IntentType.FILE_CREATE,
                "file_delete": IntentType.FILE_DELETE,
                "project_info": IntentType.PROJECT_INFO,
                "general_chat": IntentType.GENERAL_CHAT,
            }
            
            if response in intent_map:
                rule_intent.type = intent_map[response]
                rule_intent.confidence = 0.9
        except Exception:
            pass  # Fall back to rule-based
        
        return rule_intent
    
    def _extract_file_paths(self, message: str) -> List[str]:
        """Extract file paths from message."""
        paths = []
        
        for pattern in self._file_patterns:
            matches = pattern.findall(message)
            paths.extend(matches)
        
        # Deduplicate while preserving order
        seen = set()
        unique_paths = []
        for p in paths:
            if p not in seen:
                seen.add(p)
                unique_paths.append(p)
        
        return unique_paths
    
    def _detect_language(self, message: str) -> Optional[str]:
        """Detect programming language from message."""
        for lang, patterns in self._language_patterns.items():
            for pattern in patterns:
                if pattern.search(message):
                    return lang
        return None
    
    def _extract_target(self, message: str, intent: IntentType) -> str:
        """Extract the target of the action."""
        # Simple extraction - could be improved with NLP
        message_lower = message.lower()
        
        # Remove common action words
        for word in ["create", "write", "generate", "make", "build", "implement",
                     "edit", "modify", "change", "update", "fix", "review",
                     "explain", "refactor", "improve", "optimize", "test"]:
            message_lower = message_lower.replace(word, "")
        
        return message_lower.strip()
