"""Context Selector - Intelligently selects relevant context for AI prompts."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .analyzer import ContextAnalyzer, FileContext


@dataclass
class ContextConfig:
    """Configuration for context selection."""
    max_tokens: int = 8000  # Max tokens for context
    max_files: int = 10  # Max number of files to include
    include_imports: bool = True  # Include imported files
    include_dependents: bool = True  # Include files that import target
    depth: int = 2  # Depth for dependency traversal
    prioritize_recent: bool = True  # Prioritize recently modified files


@dataclass
class ContextResult:
    """Result of context selection."""
    files: List[FileContext] = field(default_factory=list)
    total_tokens: int = 0
    truncated: bool = False
    summary: str = ""
    
    def format_for_prompt(self, include_summary: bool = True) -> str:
        """Format context for inclusion in LLM prompt."""
        parts = []
        
        if include_summary and self.summary:
            parts.append(f"## Project Context\n{self.summary}\n")
        
        parts.append("## Relevant Code Files\n")
        
        for ctx in self.files:
            parts.append(f"### {ctx.path}")
            parts.append(f"```{ctx.language}")
            parts.append(ctx.content)
            parts.append("```\n")
        
        return "\n".join(parts)
    
    def format_compact(self) -> str:
        """Format context in a more compact way."""
        parts = []
        
        for ctx in self.files:
            parts.append(f"=== {ctx.path} ===")
            parts.append(ctx.content)
            parts.append("")
        
        return "\n".join(parts)
    
    def get_file_list(self) -> List[str]:
        """Get list of included file paths."""
        return [ctx.path for ctx in self.files]


class ContextSelector:
    """Selects relevant context for AI operations."""
    
    def __init__(
        self,
        root_path: Optional[Path] = None,
        config: Optional[ContextConfig] = None,
    ):
        self.root_path = Path(root_path or Path.cwd()).resolve()
        self.config = config or ContextConfig()
        self.analyzer = ContextAnalyzer(self.root_path)
    
    def select_for_file(
        self,
        file_path: str,
        query: Optional[str] = None,
    ) -> ContextResult:
        """Select context relevant to a specific file."""
        result = ContextResult()
        selected_files: List[FileContext] = []
        total_tokens = 0
        
        # Always include the target file first
        target_ctx = self.analyzer.analyze_file(file_path)
        if target_ctx:
            selected_files.append(target_ctx)
            total_tokens += target_ctx.token_estimate
        
        # Find related files
        related = self.analyzer.find_related_files(
            file_path, 
            max_files=self.config.max_files
        )
        
        # Add related files within token budget
        for rel_path in related:
            if len(selected_files) >= self.config.max_files:
                result.truncated = True
                break
            
            ctx = self.analyzer.analyze_file(rel_path)
            if not ctx:
                continue
            
            if total_tokens + ctx.token_estimate > self.config.max_tokens:
                result.truncated = True
                continue
            
            selected_files.append(ctx)
            total_tokens += ctx.token_estimate
        
        result.files = selected_files
        result.total_tokens = total_tokens
        result.summary = self._generate_summary(selected_files)
        
        return result
    
    def select_for_query(
        self,
        query: str,
        target_file: Optional[str] = None,
    ) -> ContextResult:
        """Select context relevant to a natural language query."""
        result = ContextResult()
        selected_files: List[FileContext] = []
        total_tokens = 0
        seen_files: Set[str] = set()
        
        # If target file specified, include it first
        if target_file:
            target_ctx = self.analyzer.analyze_file(target_file)
            if target_ctx:
                selected_files.append(target_ctx)
                total_tokens += target_ctx.token_estimate
                seen_files.add(target_file)
        
        # Find files matching the query
        matching_files = self.analyzer.find_files_for_query(
            query,
            max_files=self.config.max_files * 2  # Get more, then filter
        )
        
        # Add matching files within budget
        for file_path in matching_files:
            if file_path in seen_files:
                continue
            
            if len(selected_files) >= self.config.max_files:
                result.truncated = True
                break
            
            ctx = self.analyzer.analyze_file(file_path)
            if not ctx:
                continue
            
            if total_tokens + ctx.token_estimate > self.config.max_tokens:
                result.truncated = True
                continue
            
            selected_files.append(ctx)
            total_tokens += ctx.token_estimate
            seen_files.add(file_path)
        
        # If we have a target file, also include its dependencies
        if target_file and self.config.include_imports:
            related = self.analyzer.find_related_files(target_file, max_files=5)
            for rel_path in related:
                if rel_path in seen_files:
                    continue
                
                if len(selected_files) >= self.config.max_files:
                    break
                
                ctx = self.analyzer.analyze_file(rel_path)
                if not ctx:
                    continue
                
                if total_tokens + ctx.token_estimate > self.config.max_tokens:
                    continue
                
                selected_files.append(ctx)
                total_tokens += ctx.token_estimate
                seen_files.add(rel_path)
        
        result.files = selected_files
        result.total_tokens = total_tokens
        result.summary = self._generate_summary(selected_files)
        
        return result
    
    def select_explicit(
        self,
        file_paths: List[str],
        include_dependencies: bool = False,
    ) -> ContextResult:
        """Select context from explicitly specified files."""
        result = ContextResult()
        selected_files: List[FileContext] = []
        total_tokens = 0
        seen_files: Set[str] = set()
        
        # Add explicitly specified files
        for file_path in file_paths:
            if file_path in seen_files:
                continue
            
            ctx = self.analyzer.analyze_file(file_path)
            if not ctx:
                continue
            
            if total_tokens + ctx.token_estimate > self.config.max_tokens:
                result.truncated = True
                continue
            
            selected_files.append(ctx)
            total_tokens += ctx.token_estimate
            seen_files.add(file_path)
        
        # Optionally include dependencies
        if include_dependencies:
            for file_path in file_paths:
                related = self.analyzer.find_related_files(file_path, max_files=3)
                for rel_path in related:
                    if rel_path in seen_files:
                        continue
                    
                    if len(selected_files) >= self.config.max_files:
                        result.truncated = True
                        break
                    
                    ctx = self.analyzer.analyze_file(rel_path)
                    if not ctx:
                        continue
                    
                    if total_tokens + ctx.token_estimate > self.config.max_tokens:
                        continue
                    
                    selected_files.append(ctx)
                    total_tokens += ctx.token_estimate
                    seen_files.add(rel_path)
        
        result.files = selected_files
        result.total_tokens = total_tokens
        result.summary = self._generate_summary(selected_files)
        
        return result
    
    def _generate_summary(self, files: List[FileContext]) -> str:
        """Generate a summary of the selected context."""
        if not files:
            return "No context files selected."
        
        languages = set(f.language for f in files)
        total_lines = sum(len(f.content.split('\n')) for f in files)
        
        summary_parts = [
            f"Selected {len(files)} files ({total_lines} lines)",
            f"Languages: {', '.join(sorted(languages))}",
            "Files:",
        ]
        
        for f in files[:5]:
            deps = len(f.dependencies)
            exports = len(f.exports)
            summary_parts.append(f"  - {f.path} ({exports} exports, {deps} deps)")
        
        if len(files) > 5:
            summary_parts.append(f"  ... and {len(files) - 5} more files")
        
        return "\n".join(summary_parts)
    
    def get_auto_context(
        self,
        query: str,
        target_files: Optional[List[str]] = None,
    ) -> ContextResult:
        """Automatically select the best context for a query.
        
        This is the main entry point for smart context selection.
        """
        if target_files:
            # If specific files are given, use them as primary context
            result = self.select_explicit(target_files, include_dependencies=True)
            
            # Also search for query-relevant files
            query_result = self.select_for_query(query)
            
            # Merge results, avoiding duplicates
            seen = set(f.path for f in result.files)
            remaining_budget = self.config.max_tokens - result.total_tokens
            
            for ctx in query_result.files:
                if ctx.path in seen:
                    continue
                if ctx.token_estimate > remaining_budget:
                    continue
                if len(result.files) >= self.config.max_files:
                    break
                
                result.files.append(ctx)
                result.total_tokens += ctx.token_estimate
                remaining_budget -= ctx.token_estimate
            
            result.summary = self._generate_summary(result.files)
            return result
        else:
            # No target files, just use query-based selection
            return self.select_for_query(query)
