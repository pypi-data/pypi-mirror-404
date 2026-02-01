"""Git repository manager."""

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass
class GitStatus:
    """Represents the current git status."""
    staged: List[str] = field(default_factory=list)
    modified: List[str] = field(default_factory=list)
    untracked: List[str] = field(default_factory=list)
    deleted: List[str] = field(default_factory=list)
    branch: str = ""
    remote: str = ""
    ahead: int = 0
    behind: int = 0
    
    @property
    def has_changes(self) -> bool:
        return bool(self.staged or self.modified or self.untracked or self.deleted)
    
    @property
    def has_staged(self) -> bool:
        return bool(self.staged)
    
    @property
    def total_changes(self) -> int:
        return len(self.staged) + len(self.modified) + len(self.untracked) + len(self.deleted)


@dataclass
class GitDiff:
    """Represents a git diff."""
    files_changed: int = 0
    insertions: int = 0
    deletions: int = 0
    diff_text: str = ""
    file_diffs: List[dict] = field(default_factory=list)


class GitManager:
    """Manages git operations."""
    
    def __init__(self, repo_path: Optional[Path] = None):
        self.repo_path = repo_path or Path.cwd()
        self._validate_repo()
    
    def _validate_repo(self) -> None:
        """Validate that we're in a git repository."""
        if not (self.repo_path / ".git").exists():
            raise ValueError(f"Not a git repository: {self.repo_path}")
    
    def _run_git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        """Run a git command."""
        result = subprocess.run(
            ["git", *args],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )
        if check and result.returncode != 0:
            raise RuntimeError(f"Git command failed: {result.stderr}")
        return result
    
    def get_status(self) -> GitStatus:
        """Get current git status."""
        status = GitStatus()
        
        # Get branch name
        result = self._run_git("branch", "--show-current", check=False)
        status.branch = result.stdout.strip()
        
        # Get remote
        result = self._run_git("remote", check=False)
        status.remote = result.stdout.strip().split("\n")[0] if result.stdout else "origin"
        
        # Get ahead/behind
        result = self._run_git("rev-list", "--left-right", "--count", f"{status.remote}/{status.branch}...HEAD", check=False)
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split()
            if len(parts) == 2:
                status.behind, status.ahead = int(parts[0]), int(parts[1])
        
        # Get file status
        result = self._run_git("status", "--porcelain", check=False)
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            status_code = line[:2]
            file_path = line[3:]
            
            if status_code[0] in "MADRC":
                status.staged.append(file_path)
            if status_code[1] == "M":
                status.modified.append(file_path)
            elif status_code[1] == "D":
                status.deleted.append(file_path)
            elif status_code == "??":
                status.untracked.append(file_path)
        
        return status
    
    def get_diff(self, staged: bool = True) -> GitDiff:
        """Get diff of changes."""
        diff = GitDiff()
        
        # Get diff text
        if staged:
            result = self._run_git("diff", "--cached", check=False)
        else:
            result = self._run_git("diff", check=False)
        
        diff.diff_text = result.stdout
        
        # Get stats
        if staged:
            result = self._run_git("diff", "--cached", "--stat", check=False)
        else:
            result = self._run_git("diff", "--stat", check=False)
        
        # Parse stats from last line
        lines = result.stdout.strip().split("\n")
        if lines and lines[-1]:
            last_line = lines[-1]
            # Parse "X files changed, Y insertions(+), Z deletions(-)"
            import re
            match = re.search(r"(\d+) files? changed", last_line)
            if match:
                diff.files_changed = int(match.group(1))
            match = re.search(r"(\d+) insertions?", last_line)
            if match:
                diff.insertions = int(match.group(1))
            match = re.search(r"(\d+) deletions?", last_line)
            if match:
                diff.deletions = int(match.group(1))
        
        return diff
    
    def stage_all(self) -> None:
        """Stage all changes."""
        self._run_git("add", "-A")
    
    def stage_files(self, files: List[str]) -> None:
        """Stage specific files."""
        self._run_git("add", *files)
    
    def commit(self, message: str) -> str:
        """Create a commit with the given message."""
        result = self._run_git("commit", "-m", message)
        # Extract commit hash from output
        import re
        match = re.search(r"\[[\w-]+ ([a-f0-9]+)\]", result.stdout)
        return match.group(1) if match else ""
    
    def push(self, remote: str = "origin", branch: Optional[str] = None, 
             set_upstream: bool = False) -> Tuple[bool, str]:
        """Push to remote."""
        status = self.get_status()
        branch = branch or status.branch
        
        args = ["push"]
        if set_upstream:
            args.extend(["-u", remote, branch])
        else:
            args.extend([remote, branch])
        
        result = self._run_git(*args, check=False)
        success = result.returncode == 0
        output = result.stdout + result.stderr
        
        return success, output
    
    def get_recent_commits(self, count: int = 5) -> List[dict]:
        """Get recent commits."""
        result = self._run_git(
            "log", f"-{count}", 
            "--pretty=format:%H|%h|%s|%an|%ar",
            check=False
        )
        
        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|")
            if len(parts) >= 5:
                commits.append({
                    "hash": parts[0],
                    "short_hash": parts[1],
                    "message": parts[2],
                    "author": parts[3],
                    "time": parts[4],
                })
        
        return commits
    
    def get_remote_url(self) -> str:
        """Get the remote URL."""
        result = self._run_git("remote", "get-url", "origin", check=False)
        return result.stdout.strip()
