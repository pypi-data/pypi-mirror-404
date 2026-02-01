"""Context Analyzer - Analyzes file dependencies and relationships."""

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class FileContext:
    """Context information about a single file."""
    path: str
    content: str
    language: str
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)  # Functions, classes defined
    dependencies: List[str] = field(default_factory=list)  # Files this imports from
    dependents: List[str] = field(default_factory=list)  # Files that import this
    symbols: List[str] = field(default_factory=list)  # All symbols (funcs, classes, vars)
    
    @property
    def token_estimate(self) -> int:
        """Estimate token count (rough: ~4 chars per token)."""
        return len(self.content) // 4
    
    def get_summary(self) -> str:
        """Get a brief summary of the file."""
        lines = self.content.split('\n')
        return f"{self.path} ({len(lines)} lines, {self.language})"


@dataclass
class DependencyGraph:
    """Graph of file dependencies."""
    nodes: Dict[str, FileContext] = field(default_factory=dict)
    edges: Dict[str, Set[str]] = field(default_factory=dict)  # file -> imports
    reverse_edges: Dict[str, Set[str]] = field(default_factory=dict)  # file -> imported_by
    
    def add_file(self, file_ctx: FileContext) -> None:
        """Add a file to the graph."""
        self.nodes[file_ctx.path] = file_ctx
        if file_ctx.path not in self.edges:
            self.edges[file_ctx.path] = set()
        if file_ctx.path not in self.reverse_edges:
            self.reverse_edges[file_ctx.path] = set()
    
    def add_dependency(self, from_file: str, to_file: str) -> None:
        """Add a dependency edge."""
        if from_file not in self.edges:
            self.edges[from_file] = set()
        if to_file not in self.reverse_edges:
            self.reverse_edges[to_file] = set()
        
        self.edges[from_file].add(to_file)
        self.reverse_edges[to_file].add(from_file)
    
    def get_related_files(self, file_path: str, depth: int = 2) -> Set[str]:
        """Get files related to the given file up to a certain depth."""
        related = set()
        to_visit = [(file_path, 0)]
        visited = set()
        
        while to_visit:
            current, current_depth = to_visit.pop(0)
            if current in visited or current_depth > depth:
                continue
            
            visited.add(current)
            if current != file_path:
                related.add(current)
            
            # Add imports and importers
            for dep in self.edges.get(current, set()):
                if dep not in visited:
                    to_visit.append((dep, current_depth + 1))
            
            for dep in self.reverse_edges.get(current, set()):
                if dep not in visited:
                    to_visit.append((dep, current_depth + 1))
        
        return related


class ContextAnalyzer:
    """Analyzes codebase for context and dependencies."""
    
    LANGUAGE_MAP = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.c': 'c',
        '.cpp': 'cpp',
        '.h': 'c',
        '.hpp': 'cpp',
    }
    
    IGNORE_DIRS = {
        '.git', '__pycache__', 'node_modules', '.venv', 'venv',
        'env', 'dist', 'build', '.pytest_cache', '.mypy_cache',
        '.tox', 'htmlcov', '.eggs', '.idea', '.vscode',
    }
    
    def __init__(self, root_path: Optional[Path] = None):
        self.root_path = Path(root_path or Path.cwd()).resolve()
        self._graph: Optional[DependencyGraph] = None
        self._file_cache: Dict[str, FileContext] = {}
    
    def analyze_file(self, file_path: str) -> Optional[FileContext]:
        """Analyze a single file for context."""
        if file_path in self._file_cache:
            return self._file_cache[file_path]
        
        full_path = self._resolve_path(file_path)
        if not full_path.exists():
            return None
        
        try:
            content = full_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            return None
        
        language = self.LANGUAGE_MAP.get(full_path.suffix.lower(), 'text')
        
        ctx = FileContext(
            path=file_path,
            content=content,
            language=language,
        )
        
        # Parse based on language
        if language == 'python':
            self._analyze_python(ctx)
        elif language in ('javascript', 'typescript'):
            self._analyze_javascript(ctx)
        elif language == 'go':
            self._analyze_go(ctx)
        
        self._file_cache[file_path] = ctx
        return ctx
    
    def _analyze_python(self, ctx: FileContext) -> None:
        """Analyze Python file for imports and symbols."""
        try:
            tree = ast.parse(ctx.content)
        except SyntaxError:
            return
        
        for node in ast.walk(tree):
            # Imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    ctx.imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    ctx.imports.append(node.module)
            
            # Exports (top-level definitions)
            elif isinstance(node, ast.FunctionDef):
                ctx.exports.append(node.name)
                ctx.symbols.append(f"function:{node.name}")
            elif isinstance(node, ast.AsyncFunctionDef):
                ctx.exports.append(node.name)
                ctx.symbols.append(f"async_function:{node.name}")
            elif isinstance(node, ast.ClassDef):
                ctx.exports.append(node.name)
                ctx.symbols.append(f"class:{node.name}")
    
    def _analyze_javascript(self, ctx: FileContext) -> None:
        """Analyze JavaScript/TypeScript for imports."""
        # import ... from '...'
        import_pattern = r"import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]"
        # require('...')
        require_pattern = r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"
        # export function/class/const
        export_pattern = r"export\s+(?:default\s+)?(?:function|class|const|let|var)\s+(\w+)"
        
        for match in re.finditer(import_pattern, ctx.content):
            ctx.imports.append(match.group(1))
        
        for match in re.finditer(require_pattern, ctx.content):
            ctx.imports.append(match.group(1))
        
        for match in re.finditer(export_pattern, ctx.content):
            ctx.exports.append(match.group(1))
            ctx.symbols.append(f"export:{match.group(1)}")
    
    def _analyze_go(self, ctx: FileContext) -> None:
        """Analyze Go file for imports."""
        # import "..." or import (...)
        single_import = r'import\s+"([^"]+)"'
        multi_import = r'import\s+\(([\s\S]*?)\)'
        
        for match in re.finditer(single_import, ctx.content):
            ctx.imports.append(match.group(1))
        
        for match in re.finditer(multi_import, ctx.content):
            block = match.group(1)
            for line in block.split('\n'):
                line = line.strip()
                if line.startswith('"') and line.endswith('"'):
                    ctx.imports.append(line[1:-1])
        
        # func Name(...)
        func_pattern = r'func\s+(?:\([^)]+\)\s+)?(\w+)\s*\('
        for match in re.finditer(func_pattern, ctx.content):
            ctx.exports.append(match.group(1))
            ctx.symbols.append(f"func:{match.group(1)}")
    
    def build_dependency_graph(self, files: Optional[List[str]] = None) -> DependencyGraph:
        """Build a dependency graph for the codebase."""
        if self._graph and not files:
            return self._graph
        
        graph = DependencyGraph()
        
        # Get all files if not specified
        if files is None:
            files = self._get_all_code_files()
        
        # Analyze each file
        for file_path in files:
            ctx = self.analyze_file(file_path)
            if ctx:
                graph.add_file(ctx)
        
        # Resolve dependencies
        for file_path, ctx in graph.nodes.items():
            for imp in ctx.imports:
                resolved = self._resolve_import(file_path, imp)
                if resolved and resolved in graph.nodes:
                    graph.add_dependency(file_path, resolved)
                    ctx.dependencies.append(resolved)
                    graph.nodes[resolved].dependents.append(file_path)
        
        self._graph = graph
        return graph
    
    def _resolve_import(self, from_file: str, import_path: str) -> Optional[str]:
        """Resolve an import to a file path."""
        from_path = Path(from_file)
        
        # Python relative imports
        if import_path.startswith('.'):
            parts = import_path.split('.')
            up_levels = len([p for p in parts if p == ''])
            module_parts = [p for p in parts if p]
            
            base = from_path.parent
            for _ in range(up_levels - 1):
                base = base.parent
            
            for part in module_parts:
                base = base / part
            
            # Try .py extension
            candidates = [
                str(base) + '.py',
                str(base / '__init__.py'),
            ]
        else:
            # Absolute import - try to find in project
            parts = import_path.split('.')
            candidates = [
                '/'.join(parts) + '.py',
                '/'.join(parts) + '/__init__.py',
                'src/' + '/'.join(parts) + '.py',
            ]
        
        for candidate in candidates:
            if self._resolve_path(candidate).exists():
                return candidate
        
        return None
    
    def _get_all_code_files(self) -> List[str]:
        """Get all code files in the project."""
        files = []
        
        for path in self.root_path.rglob('*'):
            if path.is_file() and path.suffix.lower() in self.LANGUAGE_MAP:
                # Check if in ignored directory
                if any(part in self.IGNORE_DIRS for part in path.parts):
                    continue
                
                try:
                    rel_path = str(path.relative_to(self.root_path))
                    files.append(rel_path)
                except ValueError:
                    pass
        
        return files
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve a path relative to root."""
        p = Path(path)
        if p.is_absolute():
            return p
        return self.root_path / path
    
    def find_related_files(self, file_path: str, max_files: int = 10) -> List[str]:
        """Find files related to the given file."""
        graph = self.build_dependency_graph()
        related = graph.get_related_files(file_path, depth=2)
        
        # Sort by relevance (direct dependencies first)
        direct_deps = set(graph.edges.get(file_path, set()))
        direct_deps.update(graph.reverse_edges.get(file_path, set()))
        
        sorted_related = sorted(
            related,
            key=lambda f: (f not in direct_deps, f)
        )
        
        return sorted_related[:max_files]
    
    def find_files_for_query(self, query: str, max_files: int = 5) -> List[str]:
        """Find files relevant to a natural language query."""
        query_lower = query.lower()
        scores: Dict[str, float] = {}
        
        # Keywords to look for
        keywords = set(re.findall(r'\b\w+\b', query_lower))
        
        for file_path in self._get_all_code_files():
            ctx = self.analyze_file(file_path)
            if not ctx:
                continue
            
            score = 0.0
            
            # Check file name
            file_name = Path(file_path).stem.lower()
            for kw in keywords:
                if kw in file_name:
                    score += 3.0
            
            # Check symbols
            for symbol in ctx.symbols:
                symbol_lower = symbol.lower()
                for kw in keywords:
                    if kw in symbol_lower:
                        score += 2.0
            
            # Check content (less weight)
            content_lower = ctx.content.lower()
            for kw in keywords:
                if len(kw) > 3 and kw in content_lower:
                    score += 0.5
            
            if score > 0:
                scores[file_path] = score
        
        # Sort by score
        sorted_files = sorted(scores.keys(), key=lambda f: scores[f], reverse=True)
        return sorted_files[:max_files]
