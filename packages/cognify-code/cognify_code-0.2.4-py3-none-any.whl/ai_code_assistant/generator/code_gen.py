"""Code generator for creating code from specifications."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, List, Literal, Optional, Tuple

from ai_code_assistant.config import Config
from ai_code_assistant.llm import LLMManager
from ai_code_assistant.generator.prompts import GENERATION_PROMPTS


GenerationMode = Literal["function", "class", "script", "test", "generic"]


@dataclass
class GenerationResult:
    """Result of code generation."""
    code: str
    language: str
    mode: GenerationMode
    description: str
    raw_response: str = ""
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None and bool(self.code.strip())


class CodeGenerator:
    """Generates code from natural language descriptions."""

    def __init__(self, config: Config, llm_manager: LLMManager):
        self.config = config
        self.llm = llm_manager

    def generate_function(
        self,
        description: str,
        name: str,
        language: str = "python",
        parameters: str = "",
        return_type: str = "None",
    ) -> GenerationResult:
        """Generate a function from specification."""
        prompt = GENERATION_PROMPTS["function"]
        
        try:
            response = self.llm.invoke_with_template(
                prompt,
                language=language,
                description=description,
                name=name,
                parameters=parameters or "None specified",
                return_type=return_type,
                include_type_hints=self.config.generation.include_type_hints,
                include_docstrings=self.config.generation.include_docstrings,
            )
            code = self._extract_code(response, language)
            return GenerationResult(
                code=code,
                language=language,
                mode="function",
                description=description,
                raw_response=response,
            )
        except Exception as e:
            return GenerationResult(
                code="",
                language=language,
                mode="function",
                description=description,
                error=str(e),
            )

    def generate_class(
        self,
        description: str,
        name: str,
        language: str = "python",
        attributes: str = "",
        methods: str = "",
    ) -> GenerationResult:
        """Generate a class from specification."""
        prompt = GENERATION_PROMPTS["class"]
        
        try:
            response = self.llm.invoke_with_template(
                prompt,
                language=language,
                description=description,
                name=name,
                attributes=attributes or "None specified",
                methods=methods or "None specified",
                include_type_hints=self.config.generation.include_type_hints,
                include_docstrings=self.config.generation.include_docstrings,
            )
            code = self._extract_code(response, language)
            return GenerationResult(
                code=code,
                language=language,
                mode="class",
                description=description,
                raw_response=response,
            )
        except Exception as e:
            return GenerationResult(
                code="",
                language=language,
                mode="class",
                description=description,
                error=str(e),
            )

    def generate_script(
        self,
        description: str,
        requirements: List[str],
        language: str = "python",
    ) -> GenerationResult:
        """Generate a complete script or module."""
        prompt = GENERATION_PROMPTS["script"]
        
        try:
            response = self.llm.invoke_with_template(
                prompt,
                language=language,
                description=description,
                requirements="\n".join(f"- {r}" for r in requirements),
                include_type_hints=self.config.generation.include_type_hints,
                include_docstrings=self.config.generation.include_docstrings,
            )
            code = self._extract_code(response, language)
            return GenerationResult(
                code=code,
                language=language,
                mode="script",
                description=description,
                raw_response=response,
            )
        except Exception as e:
            return GenerationResult(
                code="",
                language=language,
                mode="script",
                description=description,
                error=str(e),
            )

    def generate_tests(
        self,
        source_code: str,
        language: str = "python",
        test_framework: str = "pytest",
    ) -> GenerationResult:
        """Generate tests for existing code."""
        prompt = GENERATION_PROMPTS["test"]
        
        try:
            response = self.llm.invoke_with_template(
                prompt,
                language=language,
                source_code=source_code,
                test_framework=test_framework,
            )
            code = self._extract_code(response, language)
            return GenerationResult(
                code=code,
                language=language,
                mode="test",
                description=f"Tests for provided {language} code",
                raw_response=response,
            )
        except Exception as e:
            return GenerationResult(
                code="",
                language=language,
                mode="test",
                description="Test generation failed",
                error=str(e),
            )

    def generate(
        self,
        description: str,
        language: str = "python",
    ) -> GenerationResult:
        """Generate code from a generic description."""
        prompt = GENERATION_PROMPTS["generic"]
        
        try:
            response = self.llm.invoke_with_template(
                prompt,
                language=language,
                description=description,
                include_type_hints=self.config.generation.include_type_hints,
                include_docstrings=self.config.generation.include_docstrings,
            )
            code = self._extract_code(response, language)
            return GenerationResult(
                code=code,
                language=language,
                mode="generic",
                description=description,
                raw_response=response,
            )
        except Exception as e:
            return GenerationResult(
                code="",
                language=language,
                mode="generic",
                description=description,
                error=str(e),
            )


    def generate_stream(
        self,
        description: str,
        mode: str = "generic",
        language: str = "python",
        name: str = "",
        parameters: str = "",
        source_code: str = "",
    ) -> Iterator[Tuple[str, bool]]:
        """
        Stream code generation with real-time output.
        
        Yields tuples of (chunk, is_complete).
        The final yield will have is_complete=True and contain the extracted code.
        """
        # Build the prompt based on mode
        if mode == "function":
            prompt_template = GENERATION_PROMPTS["function"]
            formatted = prompt_template.format(
                language=language,
                description=description,
                name=name or "generated_function",
                parameters=parameters or "None specified",
                return_type="appropriate type",
                include_type_hints=self.config.generation.include_type_hints,
                include_docstrings=self.config.generation.include_docstrings,
            )
        elif mode == "class":
            prompt_template = GENERATION_PROMPTS["class"]
            formatted = prompt_template.format(
                language=language,
                description=description,
                name=name or "GeneratedClass",
                attributes="None specified",
                methods="None specified",
                include_type_hints=self.config.generation.include_type_hints,
                include_docstrings=self.config.generation.include_docstrings,
            )
        elif mode == "script":
            prompt_template = GENERATION_PROMPTS["script"]
            formatted = prompt_template.format(
                language=language,
                description=description,
                requirements=f"- {description}",
                include_type_hints=self.config.generation.include_type_hints,
                include_docstrings=self.config.generation.include_docstrings,
            )
        elif mode == "test":
            prompt_template = GENERATION_PROMPTS["test"]
            formatted = prompt_template.format(
                language=language,
                source_code=source_code,
                test_framework="pytest",
            )
        else:  # generic
            prompt_template = GENERATION_PROMPTS["generic"]
            formatted = prompt_template.format(
                language=language,
                description=description,
                include_type_hints=self.config.generation.include_type_hints,
                include_docstrings=self.config.generation.include_docstrings,
            )

        # Stream the response
        full_response = ""
        try:
            for chunk in self.llm.stream(formatted):
                full_response += chunk
                yield (chunk, False)
            
            # Extract code and yield final result
            code = self._extract_code(full_response, language)
            yield (code, True)
        except Exception as e:
            yield (f"Error: {str(e)}", True)


    def generate_stream(
        self,
        description: str,
        mode: str = "generic",
        language: str = "python",
        name: str = "",
        parameters: str = "",
        source_code: str = "",
    ) -> Iterator[Tuple[str, bool]]:
        """
        Stream code generation with real-time output.
        
        Yields tuples of (chunk, is_complete).
        The final yield will have is_complete=True and contain the extracted code.
        """
        # Build the prompt based on mode
        if mode == "function":
            prompt_template = GENERATION_PROMPTS["function"]
            formatted = prompt_template.format(
                language=language,
                description=description,
                name=name or "generated_function",
                parameters=parameters or "None specified",
                return_type="appropriate type",
                include_type_hints=self.config.generation.include_type_hints,
                include_docstrings=self.config.generation.include_docstrings,
            )
        elif mode == "class":
            prompt_template = GENERATION_PROMPTS["class"]
            formatted = prompt_template.format(
                language=language,
                description=description,
                name=name or "GeneratedClass",
                attributes="None specified",
                methods="None specified",
                include_type_hints=self.config.generation.include_type_hints,
                include_docstrings=self.config.generation.include_docstrings,
            )
        elif mode == "script":
            prompt_template = GENERATION_PROMPTS["script"]
            formatted = prompt_template.format(
                language=language,
                description=description,
                requirements=f"- {description}",
                include_type_hints=self.config.generation.include_type_hints,
                include_docstrings=self.config.generation.include_docstrings,
            )
        elif mode == "test":
            prompt_template = GENERATION_PROMPTS["test"]
            formatted = prompt_template.format(
                language=language,
                source_code=source_code,
                test_framework="pytest",
            )
        else:  # generic
            prompt_template = GENERATION_PROMPTS["generic"]
            formatted = prompt_template.format(
                language=language,
                description=description,
                include_type_hints=self.config.generation.include_type_hints,
                include_docstrings=self.config.generation.include_docstrings,
            )

        # Stream the response
        full_response = ""
        try:
            for chunk in self.llm.stream(formatted):
                full_response += chunk
                yield (chunk, False)
            
            # Extract code and yield final result
            code = self._extract_code(full_response, language)
            yield (code, True)
        except Exception as e:
            yield (f"Error: {str(e)}", True)

    def _extract_code(self, response: str, language: str) -> str:
        """Extract code block from LLM response."""
        # Try to find language-specific code block
        pattern = rf"```{language}\s*\n(.*?)```"
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Try generic code block
        pattern = r"```\s*\n(.*?)```"
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()

        # Try any code block
        pattern = r"```\w*\s*\n(.*?)```"
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()

        # Look for code that starts with common patterns
        lines = response.strip().split('\n')
        code_lines = []
        in_code = False

        for line in lines:
            # Detect start of code
            if not in_code:
                if line.strip().startswith(('def ', 'class ', 'import ', 'from ', '#!', 'function ', 'const ', 'let ', 'var ')):
                    in_code = True

            if in_code:
                code_lines.append(line)

        if code_lines:
            return '\n'.join(code_lines).strip()

        # Return raw response if no code block found
        return response.strip()

    def save_to_file(self, result: GenerationResult, output_path: Path) -> bool:
        """Save generated code to a file."""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(result.code)
            return True
        except Exception:
            return False

