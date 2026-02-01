"""Code Generator for AI-powered code generation."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ai_code_assistant.agent.file_manager import FileContextManager, ProjectContext


@dataclass
class GeneratedCode:
    """Represents generated code."""
    code: str
    file_path: str
    language: str
    description: str
    is_new_file: bool = True
    imports: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class CodeGenerationRequest:
    """Request for code generation."""
    description: str
    language: Optional[str] = None
    file_path: Optional[str] = None
    context_files: List[str] = field(default_factory=list)
    style_guide: Optional[str] = None
    framework: Optional[str] = None


# Language-specific templates
CODE_TEMPLATES = {
    "python": {
        "function": '''def {name}({params}){return_type}:
    """{docstring}"""
    {body}
''',
        "class": '''class {name}{base}:
    """{docstring}"""
    
    def __init__(self{init_params}):
        {init_body}
    
    {methods}
''',
        "api_endpoint": '''@app.{method}("{path}")
async def {name}({params}){return_type}:
    """{docstring}"""
    {body}
''',
    },
    "typescript": {
        "function": '''export function {name}({params}): {return_type} {{
    {body}
}}
''',
        "class": '''export class {name}{base} {{
    {properties}
    
    constructor({init_params}) {{
        {init_body}
    }}
    
    {methods}
}}
''',
        "component": '''import React from 'react';

interface {name}Props {{
    {props}
}}

export const {name}: React.FC<{name}Props> = ({{ {destructured_props} }}) => {{
    return (
        {jsx}
    );
}};
''',
    },
}


GENERATION_PROMPT = '''You are an expert code generator. Generate high-quality, production-ready code based on the user's request.

## Project Context
{project_context}

## Existing Code Context
{code_context}

## User Request
{request}

## Requirements
- Language: {language}
- File path: {file_path}
- Framework: {framework}

## Instructions
1. Generate clean, well-documented code
2. Follow best practices for {language}
3. Include proper error handling
4. Add type hints/annotations where applicable
5. Include necessary imports at the top
6. Match the style of existing code in the project

## Output Format
Respond with ONLY the code, no explanations. Start with any necessary imports.
If creating a new file, include the complete file content.
If modifying existing code, show only the new/changed code.

```{language}
'''


class CodeGenerator:
    """Generates code using AI with project context awareness."""
    
    def __init__(self, llm_manager, file_manager: Optional[FileContextManager] = None):
        self.llm = llm_manager
        self.file_manager = file_manager or FileContextManager()
    
    def generate(self, request: CodeGenerationRequest) -> GeneratedCode:
        """Generate code based on the request."""
        # Get project context
        project_context = self._build_project_context()
        
        # Get code context from related files
        code_context = self._build_code_context(request)
        
        # Determine language and file path
        language = request.language or self._detect_language(request)
        file_path = request.file_path or self._suggest_file_path(request, language)
        
        # Build prompt
        prompt = GENERATION_PROMPT.format(
            project_context=project_context,
            code_context=code_context,
            request=request.description,
            language=language,
            file_path=file_path,
            framework=request.framework or "standard library",
        )
        
        # Generate code
        response = self.llm.invoke(prompt)
        
        # Parse response
        code = self._extract_code(response, language)
        imports = self._extract_imports(code, language)
        
        return GeneratedCode(
            code=code,
            file_path=file_path,
            language=language,
            description=request.description,
            is_new_file=not self.file_manager.file_exists(file_path),
            imports=imports,
        )
    
    def generate_function(self, name: str, description: str, 
                          language: str = "python",
                          params: Optional[List[Dict]] = None,
                          return_type: Optional[str] = None) -> GeneratedCode:
        """Generate a function."""
        params_str = self._format_params(params or [], language)
        
        request = CodeGenerationRequest(
            description=f"Create a function named '{name}' that {description}. "
                       f"Parameters: {params_str}. "
                       f"Return type: {return_type or 'appropriate type'}",
            language=language,
        )
        
        return self.generate(request)
    
    def generate_class(self, name: str, description: str,
                       language: str = "python",
                       methods: Optional[List[str]] = None,
                       base_class: Optional[str] = None) -> GeneratedCode:
        """Generate a class."""
        methods_str = ", ".join(methods) if methods else "appropriate methods"
        
        request = CodeGenerationRequest(
            description=f"Create a class named '{name}' that {description}. "
                       f"Include methods: {methods_str}. "
                       f"Base class: {base_class or 'none'}",
            language=language,
        )
        
        return self.generate(request)
    
    def generate_api_endpoint(self, path: str, method: str,
                              description: str,
                              framework: str = "fastapi") -> GeneratedCode:
        """Generate an API endpoint."""
        request = CodeGenerationRequest(
            description=f"Create a {method.upper()} endpoint at '{path}' that {description}",
            language="python",
            framework=framework,
        )
        
        return self.generate(request)
    
    def generate_test(self, target_file: str, 
                      test_framework: str = "pytest") -> GeneratedCode:
        """Generate tests for a file."""
        # Read the target file
        content = self.file_manager.read_file(target_file)
        
        if not content:
            raise ValueError(f"Cannot read file: {target_file}")
        
        request = CodeGenerationRequest(
            description=f"Generate comprehensive unit tests for the following code:\n\n{content[:3000]}",
            language="python",
            framework=test_framework,
            context_files=[target_file],
        )
        
        result = self.generate(request)
        
        # Suggest test file path
        if target_file.startswith("src/"):
            result.file_path = target_file.replace("src/", "tests/test_")
        else:
            result.file_path = f"tests/test_{target_file.split('/')[-1]}"
        
        return result
    
    def _build_project_context(self) -> str:
        """Build project context string."""
        context = self.file_manager.get_project_context()
        
        lines = [
            f"Project root: {context.root_path.name}",
            f"Languages: {', '.join(context.languages)}",
            f"Total files: {context.total_code_files} code files",
            "",
            "Project structure (summary):",
            self.file_manager.get_structure_summary(max_depth=2),
        ]
        
        return "\n".join(lines)
    
    def _build_code_context(self, request: CodeGenerationRequest) -> str:
        """Build code context from related files."""
        context_parts = []
        
        # Read explicitly requested context files
        for file_path in request.context_files[:5]:  # Limit to 5 files
            content = self.file_manager.read_file(file_path)
            if content:
                # Truncate large files
                if len(content) > 2000:
                    content = content[:2000] + "\n... (truncated)"
                context_parts.append(f"### {file_path}\n```\n{content}\n```")
        
        # If file_path specified, get related files
        if request.file_path:
            related = self.file_manager.get_related_files(request.file_path)
            for rel_path in related[:3]:
                if rel_path not in request.context_files:
                    content = self.file_manager.read_file(rel_path)
                    if content and len(content) < 1500:
                        context_parts.append(f"### {rel_path} (related)\n```\n{content}\n```")
        
        return "\n\n".join(context_parts) if context_parts else "No existing code context."
    
    def _detect_language(self, request: CodeGenerationRequest) -> str:
        """Detect language from request."""
        desc_lower = request.description.lower()
        
        language_keywords = {
            "python": ["python", "django", "flask", "fastapi", "pytest"],
            "typescript": ["typescript", "react", "angular", "vue", "tsx"],
            "javascript": ["javascript", "node", "express", "js"],
            "java": ["java", "spring", "maven", "gradle"],
            "go": ["go", "golang", "gin"],
            "rust": ["rust", "cargo"],
        }
        
        for lang, keywords in language_keywords.items():
            if any(kw in desc_lower for kw in keywords):
                return lang
        
        # Default based on project
        context = self.file_manager.get_project_context()
        if context.languages:
            # Return most common language
            return list(context.languages)[0]
        
        return "python"
    
    def _suggest_file_path(self, request: CodeGenerationRequest, language: str) -> str:
        """Suggest a file path for the generated code."""
        ext_map = {
            "python": ".py",
            "typescript": ".ts",
            "javascript": ".js",
            "java": ".java",
            "go": ".go",
            "rust": ".rs",
        }
        
        ext = ext_map.get(language, ".txt")
        
        # Extract a name from the description
        desc_words = request.description.lower().split()
        name_words = []
        
        skip_words = {"create", "write", "generate", "make", "build", "a", "an", "the", "that", "which", "for"}
        
        for word in desc_words[:5]:
            word = ''.join(c for c in word if c.isalnum())
            if word and word not in skip_words:
                name_words.append(word)
                if len(name_words) >= 2:
                    break
        
        name = "_".join(name_words) if name_words else "generated"
        
        return f"src/{name}{ext}"
    
    def _extract_code(self, response: str, language: str) -> str:
        """Extract code from LLM response."""
        # Try to find code block
        import re
        
        # Match ```language or ``` code blocks
        pattern = rf"```(?:{language})?\s*\n(.*?)```"
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        
        # If no code block, return cleaned response
        lines = response.strip().split("\n")
        
        # Remove common non-code prefixes
        cleaned = []
        for line in lines:
            if not line.startswith(("Here", "This", "I'll", "The following", "```")):
                cleaned.append(line)
        
        return "\n".join(cleaned).strip()
    
    def _extract_imports(self, code: str, language: str) -> List[str]:
        """Extract import statements from code."""
        imports = []
        
        for line in code.split("\n"):
            line = line.strip()
            
            if language == "python":
                if line.startswith("import ") or line.startswith("from "):
                    imports.append(line)
            elif language in ("typescript", "javascript"):
                if line.startswith("import "):
                    imports.append(line)
            elif language == "java":
                if line.startswith("import "):
                    imports.append(line)
            elif language == "go":
                if line.startswith("import "):
                    imports.append(line)
        
        return imports
    
    def _format_params(self, params: List[Dict], language: str) -> str:
        """Format parameters for display."""
        if not params:
            return "none"
        
        formatted = []
        for p in params:
            name = p.get("name", "param")
            ptype = p.get("type", "")
            
            if language == "python":
                formatted.append(f"{name}: {ptype}" if ptype else name)
            elif language in ("typescript", "javascript"):
                formatted.append(f"{name}: {ptype}" if ptype else name)
            else:
                formatted.append(f"{ptype} {name}" if ptype else name)
        
        return ", ".join(formatted)
