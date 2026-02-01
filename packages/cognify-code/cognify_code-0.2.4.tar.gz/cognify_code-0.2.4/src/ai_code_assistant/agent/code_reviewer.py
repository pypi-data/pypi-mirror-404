"""Code Reviewer for AI-powered code analysis."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from ai_code_assistant.agent.file_manager import FileContextManager


class IssueSeverity(Enum):
    """Severity levels for code issues."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueCategory(Enum):
    """Categories of code issues."""
    SECURITY = "security"
    BUG = "bug"
    PERFORMANCE = "performance"
    STYLE = "style"
    MAINTAINABILITY = "maintainability"
    BEST_PRACTICE = "best_practice"
    ERROR_HANDLING = "error_handling"
    DOCUMENTATION = "documentation"


@dataclass
class CodeIssue:
    """Represents a code issue found during review."""
    severity: IssueSeverity
    category: IssueCategory
    message: str
    line_number: Optional[int] = None
    line_content: str = ""
    suggestion: str = ""
    fixed_code: str = ""
    
    @property
    def severity_icon(self) -> str:
        icons = {
            IssueSeverity.CRITICAL: "🔴",
            IssueSeverity.HIGH: "🟠",
            IssueSeverity.MEDIUM: "��",
            IssueSeverity.LOW: "🔵",
            IssueSeverity.INFO: "⚪",
        }
        return icons.get(self.severity, "⚪")
    
    def format(self) -> str:
        """Format issue for display."""
        lines = [
            f"{self.severity_icon} [{self.severity.value.upper()}] {self.message}"
        ]
        if self.line_number:
            lines.append(f"   Line {self.line_number}: {self.line_content[:60]}")
        if self.suggestion:
            lines.append(f"   → {self.suggestion}")
        return "\n".join(lines)


@dataclass
class ReviewResult:
    """Result of a code review."""
    file_path: str
    issues: List[CodeIssue] = field(default_factory=list)
    summary: str = ""
    score: int = 100  # 0-100 quality score
    reviewed_lines: int = 0
    
    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.CRITICAL)
    
    @property
    def high_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.HIGH)
    
    @property
    def medium_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.MEDIUM)
    
    @property
    def low_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.LOW)
    
    @property
    def has_critical_issues(self) -> bool:
        return self.critical_count > 0
    
    def format_summary(self) -> str:
        """Format review summary."""
        lines = [
            f"📋 Code Review: {self.file_path}",
            f"   Score: {self.score}/100",
            f"   Issues: 🔴{self.critical_count} 🟠{self.high_count} 🟡{self.medium_count} 🔵{self.low_count}",
            "",
        ]
        
        if self.summary:
            lines.append(f"Summary: {self.summary}")
            lines.append("")
        
        return "\n".join(lines)


REVIEW_PROMPT = '''You are an expert code reviewer. Analyze the following code and identify issues.

## Code to Review
File: {file_path}
Language: {language}

```{language}
{code}
```

## Review Focus Areas
1. **Security**: SQL injection, XSS, authentication issues, secrets exposure
2. **Bugs**: Logic errors, null references, race conditions, edge cases
3. **Performance**: Inefficient algorithms, memory leaks, N+1 queries
4. **Error Handling**: Missing try/catch, unhandled exceptions
5. **Best Practices**: Code style, naming conventions, SOLID principles
6. **Maintainability**: Code complexity, duplication, documentation

## Output Format
For each issue found, provide:
- SEVERITY: critical/high/medium/low/info
- CATEGORY: security/bug/performance/style/maintainability/best_practice/error_handling/documentation
- LINE: line number (if applicable)
- MESSAGE: brief description of the issue
- SUGGESTION: how to fix it
- FIXED_CODE: corrected code snippet (if applicable)

Format each issue as:
```
ISSUE:
SEVERITY: <severity>
CATEGORY: <category>
LINE: <number or "N/A">
MESSAGE: <description>
SUGGESTION: <fix recommendation>
FIXED_CODE:
<code if applicable>
END_ISSUE
```

After all issues, provide:
```
SUMMARY: <overall assessment>
SCORE: <0-100>
```

If no issues found, respond with:
```
SUMMARY: Code looks good! No significant issues found.
SCORE: 95
```
'''


class CodeReviewer:
    """Reviews code for issues and suggests improvements."""
    
    def __init__(self, llm_manager, file_manager: Optional[FileContextManager] = None):
        self.llm = llm_manager
        self.file_manager = file_manager or FileContextManager()
    
    def review_file(self, file_path: str, 
                    focus_areas: Optional[List[IssueCategory]] = None) -> ReviewResult:
        """Review a file for issues."""
        content = self.file_manager.read_file(file_path)
        
        if not content:
            raise ValueError(f"Cannot read file: {file_path}")
        
        return self.review_code(content, file_path, focus_areas)
    
    def review_code(self, code: str, file_path: str = "code",
                    focus_areas: Optional[List[IssueCategory]] = None) -> ReviewResult:
        """Review code content for issues."""
        # Detect language
        language = self._detect_language(file_path)
        
        # Build prompt
        prompt = REVIEW_PROMPT.format(
            file_path=file_path,
            language=language,
            code=code[:8000],  # Limit code size
        )
        
        # Get review from LLM
        response = self.llm.invoke(prompt)
        
        # Parse response
        result = self._parse_review_response(response, file_path, code)
        
        # Filter by focus areas if specified
        if focus_areas:
            result.issues = [i for i in result.issues if i.category in focus_areas]
        
        return result
    
    def quick_review(self, file_path: str) -> str:
        """Get a quick review summary."""
        result = self.review_file(file_path)
        return result.format_summary()
    
    def security_review(self, file_path: str) -> ReviewResult:
        """Focus on security issues only."""
        return self.review_file(file_path, focus_areas=[IssueCategory.SECURITY])
    
    def get_fix_suggestions(self, file_path: str) -> List[dict]:
        """Get actionable fix suggestions for a file."""
        result = self.review_file(file_path)
        
        suggestions = []
        for issue in result.issues:
            if issue.fixed_code:
                suggestions.append({
                    "line": issue.line_number,
                    "original": issue.line_content,
                    "fixed": issue.fixed_code,
                    "reason": issue.message,
                })
        
        return suggestions
    
    def _detect_language(self, file_path: str) -> str:
        """Detect language from file extension."""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php",
            ".c": "c",
            ".cpp": "cpp",
            ".cs": "csharp",
        }
        
        for ext, lang in ext_map.items():
            if file_path.endswith(ext):
                return lang
        
        return "text"
    
    def _parse_review_response(self, response: str, file_path: str, code: str) -> ReviewResult:
        """Parse LLM response into ReviewResult."""
        result = ReviewResult(
            file_path=file_path,
            reviewed_lines=code.count("\n") + 1,
        )
        
        # Parse issues
        import re
        
        issue_pattern = r"ISSUE:\s*\n(.*?)END_ISSUE"
        issue_matches = re.findall(issue_pattern, response, re.DOTALL)
        
        for issue_text in issue_matches:
            issue = self._parse_issue(issue_text, code)
            if issue:
                result.issues.append(issue)
        
        # Parse summary and score
        summary_match = re.search(r"SUMMARY:\s*(.+?)(?:\n|$)", response)
        if summary_match:
            result.summary = summary_match.group(1).strip()
        
        score_match = re.search(r"SCORE:\s*(\d+)", response)
        if score_match:
            result.score = min(100, max(0, int(score_match.group(1))))
        else:
            # Calculate score based on issues
            result.score = self._calculate_score(result.issues)
        
        return result
    
    def _parse_issue(self, issue_text: str, code: str) -> Optional[CodeIssue]:
        """Parse a single issue from text."""
        import re
        
        # Extract fields
        severity_match = re.search(r"SEVERITY:\s*(\w+)", issue_text, re.IGNORECASE)
        category_match = re.search(r"CATEGORY:\s*(\w+)", issue_text, re.IGNORECASE)
        line_match = re.search(r"LINE:\s*(\d+|N/A)", issue_text, re.IGNORECASE)
        message_match = re.search(r"MESSAGE:\s*(.+?)(?:\n|SUGGESTION)", issue_text, re.DOTALL)
        suggestion_match = re.search(r"SUGGESTION:\s*(.+?)(?:\n|FIXED_CODE|$)", issue_text, re.DOTALL)
        fixed_match = re.search(r"FIXED_CODE:\s*\n?(.*?)(?:END_ISSUE|$)", issue_text, re.DOTALL)
        
        if not message_match:
            return None
        
        # Map severity
        severity_map = {
            "critical": IssueSeverity.CRITICAL,
            "high": IssueSeverity.HIGH,
            "medium": IssueSeverity.MEDIUM,
            "low": IssueSeverity.LOW,
            "info": IssueSeverity.INFO,
        }
        severity = IssueSeverity.MEDIUM
        if severity_match:
            severity = severity_map.get(severity_match.group(1).lower(), IssueSeverity.MEDIUM)
        
        # Map category
        category_map = {
            "security": IssueCategory.SECURITY,
            "bug": IssueCategory.BUG,
            "performance": IssueCategory.PERFORMANCE,
            "style": IssueCategory.STYLE,
            "maintainability": IssueCategory.MAINTAINABILITY,
            "best_practice": IssueCategory.BEST_PRACTICE,
            "error_handling": IssueCategory.ERROR_HANDLING,
            "documentation": IssueCategory.DOCUMENTATION,
        }
        category = IssueCategory.BEST_PRACTICE
        if category_match:
            category = category_map.get(category_match.group(1).lower(), IssueCategory.BEST_PRACTICE)
        
        # Get line number and content
        line_number = None
        line_content = ""
        if line_match and line_match.group(1) != "N/A":
            try:
                line_number = int(line_match.group(1))
                code_lines = code.split("\n")
                if 0 < line_number <= len(code_lines):
                    line_content = code_lines[line_number - 1].strip()
            except ValueError:
                pass
        
        return CodeIssue(
            severity=severity,
            category=category,
            message=message_match.group(1).strip() if message_match else "",
            line_number=line_number,
            line_content=line_content,
            suggestion=suggestion_match.group(1).strip() if suggestion_match else "",
            fixed_code=fixed_match.group(1).strip() if fixed_match else "",
        )
    
    def _calculate_score(self, issues: List[CodeIssue]) -> int:
        """Calculate quality score based on issues."""
        score = 100
        
        for issue in issues:
            if issue.severity == IssueSeverity.CRITICAL:
                score -= 25
            elif issue.severity == IssueSeverity.HIGH:
                score -= 15
            elif issue.severity == IssueSeverity.MEDIUM:
                score -= 8
            elif issue.severity == IssueSeverity.LOW:
                score -= 3
        
        return max(0, score)
