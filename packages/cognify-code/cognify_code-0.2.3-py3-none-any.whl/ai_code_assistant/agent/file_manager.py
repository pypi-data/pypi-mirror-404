"""File Context Manager for reading/writing project files."""

import fnmatch
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set


# Common patterns to ignore
DEFAULT_IGNORE_PATTERNS = [
    ".git", ".git/*", "__pycache__", "__pycache__/*", "*.pyc",
    ".venv", ".venv/*", "venv", "venv/*", "env", "env/*",
    "node_modules", "node_modules/*", ".next", ".next/*",
    "dist", "dist/*", "build", "build/*", ".cache", ".cache/*",
    "*.egg-info", "*.egg-info/*", ".eggs", ".eggs/*",
    ".pytest_cache", ".pytest_cache/*", ".mypy_cache", ".mypy_cache/*",
    ".tox", ".tox/*", ".coverage", "htmlcov", "htmlcov/*",
    "*.log", "*.tmp", "*.temp", ".DS_Store", "Thumbs.db",
    "*.min.js", "*.min.css", "*.map",
]

# File extensions we can work with
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".rb", ".php", ".swift",
    ".kt", ".scala", ".r", ".sql", ".sh", ".bash", ".zsh",
    ".yaml", ".yml", ".json", ".toml", ".xml", ".html", ".css",
    ".scss", ".sass", ".less", ".md", ".rst", ".txt",
}


@dataclass
class FileInfo:
    """Information about a file."""
    path: Path
    relative_path: str
    extension: str
    size: int
    is_code: bool
    
    @property
    def language(self) -> str:
        """Detect language from extension."""
        ext_to_lang = {
            ".py": "python", ".js": "javascript", ".ts": "typescript",
            ".jsx": "javascript", ".tsx": "typescript", ".java": "java",
            ".go": "go", ".rs": "rust", ".c": "c", ".cpp": "cpp",
            ".h": "c", ".hpp": "cpp", ".cs": "csharp", ".rb": "ruby",
            ".php": "php", ".swift": "swift", ".kt": "kotlin",
            ".scala": "scala", ".r": "r", ".sql": "sql",
            ".sh": "bash", ".bash": "bash", ".zsh": "zsh",
            ".yaml": "yaml", ".yml": "yaml", ".json": "json",
            ".toml": "toml", ".xml": "xml", ".html": "html",
            ".css": "css", ".scss": "scss", ".md": "markdown",
        }
        return ext_to_lang.get(self.extension, "text")


@dataclass
class ProjectContext:
    """Context about the current project."""
    root_path: Path
    files: List[FileInfo] = field(default_factory=list)
    structure: str = ""
    languages: Set[str] = field(default_factory=set)
    total_files: int = 0
    total_code_files: int = 0
    
    def get_files_by_language(self, language: str) -> List[FileInfo]:
        """Get all files of a specific language."""
        return [f for f in self.files if f.language == language]
    
    def get_files_by_pattern(self, pattern: str) -> List[FileInfo]:
        """Get files matching a glob pattern."""
        return [f for f in self.files if fnmatch.fnmatch(f.relative_path, pattern)]


class FileContextManager:
    """Manages file operations and project context."""
    
    def __init__(self, root_path: Optional[Path] = None, 
                 ignore_patterns: Optional[List[str]] = None):
        self.root_path = Path(root_path or os.getcwd()).resolve()
        self.ignore_patterns = ignore_patterns or DEFAULT_IGNORE_PATTERNS
        self._context: Optional[ProjectContext] = None
    
    def _should_ignore(self, path: Path) -> bool:
        """Check if a path should be ignored."""
        rel_path = str(path.relative_to(self.root_path))
        name = path.name
        
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(rel_path, pattern):
                return True
        return False
    
    def _is_code_file(self, path: Path) -> bool:
        """Check if a file is a code file."""
        return path.suffix.lower() in CODE_EXTENSIONS
    
    def get_project_context(self, refresh: bool = False) -> ProjectContext:
        """Get or build project context."""
        if self._context and not refresh:
            return self._context
        
        context = ProjectContext(root_path=self.root_path)
        structure_lines = []
        
        for root, dirs, files in os.walk(self.root_path):
            root_path = Path(root)
            
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if not self._should_ignore(root_path / d)]
            
            # Calculate depth for indentation
            rel_root = root_path.relative_to(self.root_path)
            depth = len(rel_root.parts)
            indent = "  " * depth
            
            if depth > 0:
                structure_lines.append(f"{indent[:-2]}📁 {root_path.name}/")
            
            for file in sorted(files):
                file_path = root_path / file
                
                if self._should_ignore(file_path):
                    continue
                
                rel_path = str(file_path.relative_to(self.root_path))
                is_code = self._is_code_file(file_path)
                
                try:
                    size = file_path.stat().st_size
                except OSError:
                    size = 0
                
                file_info = FileInfo(
                    path=file_path,
                    relative_path=rel_path,
                    extension=file_path.suffix.lower(),
                    size=size,
                    is_code=is_code,
                )
                
                context.files.append(file_info)
                context.total_files += 1
                
                if is_code:
                    context.total_code_files += 1
                    context.languages.add(file_info.language)
                
                icon = "📄" if is_code else "📋"
                structure_lines.append(f"{indent}{icon} {file}")
        
        context.structure = "\n".join(structure_lines)
        self._context = context
        return context
    
    def read_file(self, path: str) -> Optional[str]:
        """Read a file's content."""
        file_path = self._resolve_path(path)
        
        if not file_path.exists():
            return None
        
        try:
            return file_path.read_text(encoding="utf-8")
        except Exception:
            return None
    
    def write_file(self, path: str, content: str, create_dirs: bool = True) -> bool:
        """Write content to a file."""
        file_path = self._resolve_path(path)
        
        try:
            if create_dirs:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_path.write_text(content, encoding="utf-8")
            
            # Invalidate context cache
            self._context = None
            return True
        except Exception:
            return False
    
    def file_exists(self, path: str) -> bool:
        """Check if a file exists."""
        return self._resolve_path(path).exists()
    
    def delete_file(self, path: str) -> bool:
        """Delete a file."""
        file_path = self._resolve_path(path)
        
        try:
            if file_path.exists():
                file_path.unlink()
                self._context = None
                return True
            return False
        except Exception:
            return False
    
    def find_files(self, pattern: str) -> List[str]:
        """Find files matching a glob pattern."""
        context = self.get_project_context()
        matches = []
        
        for file_info in context.files:
            if fnmatch.fnmatch(file_info.relative_path, pattern):
                matches.append(file_info.relative_path)
            elif fnmatch.fnmatch(file_info.path.name, pattern):
                matches.append(file_info.relative_path)
        
        return matches
    
    def get_file_info(self, path: str) -> Optional[FileInfo]:
        """Get information about a specific file."""
        file_path = self._resolve_path(path)
        
        if not file_path.exists():
            return None
        
        rel_path = str(file_path.relative_to(self.root_path))
        
        return FileInfo(
            path=file_path,
            relative_path=rel_path,
            extension=file_path.suffix.lower(),
            size=file_path.stat().st_size,
            is_code=self._is_code_file(file_path),
        )
    
    def get_related_files(self, path: str, max_files: int = 5) -> List[str]:
        """Find files related to the given file (same directory, imports, etc.)."""
        file_path = self._resolve_path(path)
        related = []
        
        # Same directory files
        if file_path.parent.exists():
            for sibling in file_path.parent.iterdir():
                if sibling.is_file() and sibling != file_path:
                    if self._is_code_file(sibling) and not self._should_ignore(sibling):
                        related.append(str(sibling.relative_to(self.root_path)))
        
        # TODO: Parse imports and find imported files
        
        return related[:max_files]
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve a path relative to root."""
        p = Path(path)
        if p.is_absolute():
            return p
        return self.root_path / path
    
    def get_structure_summary(self, max_depth: int = 3) -> str:
        """Get a summarized project structure."""
        lines = [f"📁 {self.root_path.name}/"]
        
        def walk_dir(dir_path: Path, depth: int = 1):
            if depth > max_depth:
                return
            
            try:
                items = sorted(dir_path.iterdir(), key=lambda x: (x.is_file(), x.name))
            except PermissionError:
                return
            
            dirs = []
            files = []
            
            for item in items:
                if self._should_ignore(item):
                    continue
                
                if item.is_dir():
                    dirs.append(item)
                elif item.is_file():
                    files.append(item)
            
            indent = "  " * depth
            
            for d in dirs[:10]:  # Limit directories shown
                lines.append(f"{indent}�� {d.name}/")
                walk_dir(d, depth + 1)
            
            if len(dirs) > 10:
                lines.append(f"{indent}... and {len(dirs) - 10} more directories")
            
            for f in files[:10]:  # Limit files shown
                icon = "📄" if self._is_code_file(f) else "📋"
                lines.append(f"{indent}{icon} {f.name}")
            
            if len(files) > 10:
                lines.append(f"{indent}... and {len(files) - 10} more files")
        
        walk_dir(self.root_path)
        return "\n".join(lines)
