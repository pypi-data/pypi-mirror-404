"""AI-powered commit message generator."""

from typing import Optional

from ai_code_assistant.git.manager import GitManager, GitDiff, GitStatus


COMMIT_MESSAGE_PROMPT = """Analyze the following git diff and generate a concise, descriptive commit message.

Follow these conventions:
1. Start with a type prefix: feat, fix, docs, style, refactor, test, chore
2. Use imperative mood ("Add feature" not "Added feature")
3. Keep the first line under 72 characters
4. If needed, add a blank line and bullet points for details

Git Status:
- Branch: {branch}
- Files changed: {files_changed}
- Insertions: {insertions}
- Deletions: {deletions}

Changed files:
{changed_files}

Diff (truncated to 3000 chars):
```
{diff}
```

Generate ONLY the commit message, nothing else. No explanations, no markdown formatting around it.
"""


class CommitMessageGenerator:
    """Generates commit messages using AI."""
    
    def __init__(self, llm_manager):
        self.llm = llm_manager
    
    def generate(self, git_manager: GitManager, 
                 staged_only: bool = True,
                 style: str = "conventional") -> str:
        """Generate a commit message based on the current changes.
        
        Args:
            git_manager: GitManager instance
            staged_only: If True, only consider staged changes
            style: Commit message style (conventional, simple)
            
        Returns:
            Generated commit message
        """
        status = git_manager.get_status()
        diff = git_manager.get_diff(staged=staged_only)
        
        if not diff.diff_text and not status.untracked:
            return ""
        
        # Build list of changed files
        changed_files = []
        if staged_only:
            changed_files = status.staged
        else:
            changed_files = status.staged + status.modified + status.untracked
        
        changed_files_str = "\n".join(f"  - {f}" for f in changed_files[:20])
        if len(changed_files) > 20:
            changed_files_str += f"\n  ... and {len(changed_files) - 20} more files"
        
        # Truncate diff to avoid token limits
        diff_text = diff.diff_text[:3000]
        if len(diff.diff_text) > 3000:
            diff_text += "\n... (truncated)"
        
        prompt = COMMIT_MESSAGE_PROMPT.format(
            branch=status.branch,
            files_changed=diff.files_changed or len(changed_files),
            insertions=diff.insertions,
            deletions=diff.deletions,
            changed_files=changed_files_str,
            diff=diff_text,
        )
        
        # Generate message
        response = self.llm.invoke(prompt)
        
        # Clean up response
        message = response.strip()
        # Remove any markdown code blocks if present
        if message.startswith("```"):
            lines = message.split("\n")
            message = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
        
        return message.strip()
    
    def generate_from_description(self, description: str, 
                                   git_manager: Optional[GitManager] = None) -> str:
        """Generate a commit message from a description.
        
        Args:
            description: User's description of changes
            git_manager: Optional GitManager for context
            
        Returns:
            Generated commit message
        """
        context = ""
        if git_manager:
            status = git_manager.get_status()
            diff = git_manager.get_diff(staged=True)
            context = f"""
Context:
- Branch: {status.branch}
- Files changed: {diff.files_changed}
- Staged files: {', '.join(status.staged[:5])}
"""
        
        prompt = f"""Convert this description into a proper git commit message.

Follow conventional commits format:
- Start with type: feat, fix, docs, style, refactor, test, chore
- Use imperative mood
- Keep first line under 72 characters
{context}
Description: {description}

Generate ONLY the commit message, nothing else:"""
        
        response = self.llm.invoke(prompt)
        return response.strip()
