"""Diff Engine for showing and applying code changes."""

import difflib
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple


class ChangeType(Enum):
    """Type of file change."""
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    RENAME = "rename"


@dataclass
class FileDiff:
    """Represents a diff for a single file."""
    file_path: str
    change_type: ChangeType
    original_content: str = ""
    new_content: str = ""
    diff_lines: List[str] = field(default_factory=list)
    additions: int = 0
    deletions: int = 0
    
    @property
    def has_changes(self) -> bool:
        return self.original_content != self.new_content
    
    @property
    def summary(self) -> str:
        if self.change_type == ChangeType.CREATE:
            return f"📄 {self.file_path} (new file, +{self.additions} lines)"
        elif self.change_type == ChangeType.DELETE:
            return f"🗑️  {self.file_path} (deleted, -{self.deletions} lines)"
        else:
            return f"📝 {self.file_path} (+{self.additions}/-{self.deletions})"


@dataclass
class ChangeSet:
    """A set of file changes to apply."""
    description: str
    diffs: List[FileDiff] = field(default_factory=list)
    
    @property
    def total_additions(self) -> int:
        return sum(d.additions for d in self.diffs)
    
    @property
    def total_deletions(self) -> int:
        return sum(d.deletions for d in self.diffs)
    
    @property
    def files_changed(self) -> int:
        return len(self.diffs)
    
    def add_file_change(self, file_path: str, new_content: str, 
                        original_content: str = "") -> FileDiff:
        """Add a file change to the set."""
        if not original_content and new_content:
            change_type = ChangeType.CREATE
        elif original_content and not new_content:
            change_type = ChangeType.DELETE
        else:
            change_type = ChangeType.MODIFY
        
        diff = FileDiff(
            file_path=file_path,
            change_type=change_type,
            original_content=original_content,
            new_content=new_content,
        )
        
        self.diffs.append(diff)
        return diff


class DiffEngine:
    """Engine for creating and applying diffs."""
    
    def __init__(self, file_manager=None):
        self.file_manager = file_manager
    
    def create_diff(self, original: str, modified: str, 
                    file_path: str = "file") -> FileDiff:
        """Create a diff between original and modified content."""
        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)
        
        # Generate unified diff
        diff_lines = list(difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm="",
        ))
        
        # Count additions and deletions
        additions = sum(1 for line in diff_lines if line.startswith("+") and not line.startswith("+++"))
        deletions = sum(1 for line in diff_lines if line.startswith("-") and not line.startswith("---"))
        
        # Determine change type
        if not original and modified:
            change_type = ChangeType.CREATE
        elif original and not modified:
            change_type = ChangeType.DELETE
        else:
            change_type = ChangeType.MODIFY
        
        return FileDiff(
            file_path=file_path,
            change_type=change_type,
            original_content=original,
            new_content=modified,
            diff_lines=diff_lines,
            additions=additions,
            deletions=deletions,
        )
    
    def create_file_diff(self, file_path: str, new_content: str) -> FileDiff:
        """Create a diff for a file, reading original from disk."""
        original = ""
        if self.file_manager:
            original = self.file_manager.read_file(file_path) or ""
        
        return self.create_diff(original, new_content, file_path)
    
    def format_diff(self, diff: FileDiff, color: bool = True, 
                    context_lines: int = 3) -> str:
        """Format a diff for display."""
        if not diff.diff_lines:
            # Generate diff lines if not present
            diff = self.create_diff(
                diff.original_content, 
                diff.new_content, 
                diff.file_path
            )
        
        lines = []
        
        # Header
        if diff.change_type == ChangeType.CREATE:
            header = f"📄 New file: {diff.file_path}"
        elif diff.change_type == ChangeType.DELETE:
            header = f"🗑️  Delete: {diff.file_path}"
        else:
            header = f"📝 Modified: {diff.file_path}"
        
        lines.append(header)
        lines.append("─" * 60)
        
        # Diff content
        for line in diff.diff_lines:
            if color:
                if line.startswith("+") and not line.startswith("+++"):
                    lines.append(f"[green]{line}[/green]")
                elif line.startswith("-") and not line.startswith("---"):
                    lines.append(f"[red]{line}[/red]")
                elif line.startswith("@@"):
                    lines.append(f"[cyan]{line}[/cyan]")
                else:
                    lines.append(line)
            else:
                lines.append(line)
        
        # Summary
        lines.append("─" * 60)
        lines.append(f"+{diff.additions} additions, -{diff.deletions} deletions")
        
        return "\n".join(lines)
    
    def format_diff_simple(self, diff: FileDiff) -> str:
        """Format diff in a simple, readable way."""
        lines = []
        
        if diff.change_type == ChangeType.CREATE:
            lines.append(f"📄 {diff.file_path} (new file)")
            lines.append("┌" + "─" * 58 + "┐")
            for i, line in enumerate(diff.new_content.split("\n")[:30]):
                lines.append(f"│ {line[:56]:<56} │")
            if diff.new_content.count("\n") > 30:
                lines.append(f"│ {'... (truncated)':<56} │")
            lines.append("└" + "─" * 58 + "┘")
        else:
            lines.append(f"📝 {diff.file_path}")
            lines.append("─" * 60)
            
            # Show only changed sections
            for line in diff.diff_lines[:50]:
                if line.startswith("+") and not line.startswith("+++"):
                    lines.append(f"[green]+ {line[1:]}[/green]")
                elif line.startswith("-") and not line.startswith("---"):
                    lines.append(f"[red]- {line[1:]}[/red]")
                elif line.startswith("@@"):
                    lines.append(f"[dim]{line}[/dim]")
            
            if len(diff.diff_lines) > 50:
                lines.append("[dim]... (more changes)[/dim]")
        
        return "\n".join(lines)
    
    def format_changeset(self, changeset: ChangeSet, detailed: bool = False) -> str:
        """Format a complete changeset for display."""
        lines = [
            f"📦 {changeset.description}",
            f"   {changeset.files_changed} file(s), "
            f"+{changeset.total_additions}/-{changeset.total_deletions}",
            "",
        ]
        
        for diff in changeset.diffs:
            if detailed:
                lines.append(self.format_diff_simple(diff))
            else:
                lines.append(f"  {diff.summary}")
            lines.append("")
        
        return "\n".join(lines)
    
    def apply_diff(self, diff: FileDiff) -> bool:
        """Apply a diff to the filesystem."""
        if not self.file_manager:
            raise RuntimeError("No file manager configured")
        
        if diff.change_type == ChangeType.DELETE:
            return self.file_manager.delete_file(diff.file_path)
        else:
            return self.file_manager.write_file(diff.file_path, diff.new_content)
    
    def apply_changeset(self, changeset: ChangeSet) -> Tuple[int, int]:
        """Apply all changes in a changeset.
        
        Returns:
            Tuple of (successful, failed) counts
        """
        successful = 0
        failed = 0
        
        for diff in changeset.diffs:
            try:
                if self.apply_diff(diff):
                    successful += 1
                else:
                    failed += 1
            except Exception:
                failed += 1
        
        return successful, failed
    
    def preview_changes(self, changeset: ChangeSet) -> str:
        """Generate a preview of changes to be applied."""
        lines = [
            "┌" + "─" * 58 + "┐",
            f"│ {'CHANGE PREVIEW':^56} │",
            "├" + "─" * 58 + "┤",
        ]
        
        for diff in changeset.diffs:
            icon = {
                ChangeType.CREATE: "📄",
                ChangeType.MODIFY: "📝",
                ChangeType.DELETE: "🗑️ ",
            }.get(diff.change_type, "📋")
            
            action = {
                ChangeType.CREATE: "CREATE",
                ChangeType.MODIFY: "MODIFY",
                ChangeType.DELETE: "DELETE",
            }.get(diff.change_type, "CHANGE")
            
            path_display = diff.file_path[:40]
            if len(diff.file_path) > 40:
                path_display = "..." + diff.file_path[-37:]
            
            lines.append(f"│ {icon} {action:<8} {path_display:<44} │")
            lines.append(f"│   {'+' + str(diff.additions):<6} {'-' + str(diff.deletions):<6} {'':38} │")
        
        lines.append("├" + "─" * 58 + "┤")
        lines.append(f"│ Total: {changeset.files_changed} files, "
                    f"+{changeset.total_additions}/-{changeset.total_deletions}{'':20} │")
        lines.append("└" + "─" * 58 + "┘")
        
        return "\n".join(lines)
    
    def get_inline_diff(self, original: str, modified: str) -> List[Tuple[str, str]]:
        """Get inline diff showing word-level changes.
        
        Returns list of (type, text) tuples where type is 'equal', 'insert', or 'delete'.
        """
        matcher = difflib.SequenceMatcher(None, original.split(), modified.split())
        result = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                result.append(("equal", " ".join(original.split()[i1:i2])))
            elif tag == "replace":
                result.append(("delete", " ".join(original.split()[i1:i2])))
                result.append(("insert", " ".join(modified.split()[j1:j2])))
            elif tag == "delete":
                result.append(("delete", " ".join(original.split()[i1:i2])))
            elif tag == "insert":
                result.append(("insert", " ".join(modified.split()[j1:j2])))
        
        return result
