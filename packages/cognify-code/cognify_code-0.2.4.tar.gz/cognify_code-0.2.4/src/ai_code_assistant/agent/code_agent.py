"""Code Agent - Main orchestrator for code generation, review, and editing."""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator, List, Optional, Tuple

from ai_code_assistant.agent.file_manager import FileContextManager
from ai_code_assistant.agent.intent_classifier import IntentClassifier, Intent, IntentType
from ai_code_assistant.agent.code_generator import CodeGenerator, CodeGenerationRequest, GeneratedCode
from ai_code_assistant.agent.diff_engine import DiffEngine, ChangeSet, FileDiff
from ai_code_assistant.agent.code_reviewer import CodeReviewer, ReviewResult


@dataclass
class AgentResponse:
    """Response from the code agent."""
    message: str
    intent: Optional[Intent] = None
    generated_code: Optional[GeneratedCode] = None
    review_result: Optional[ReviewResult] = None
    changeset: Optional[ChangeSet] = None
    requires_confirmation: bool = False
    action_callback: Optional[Callable] = None
    
    @property
    def has_changes(self) -> bool:
        return self.changeset is not None and self.changeset.files_changed > 0


class CodeAgent:
    """Main agent that orchestrates code operations based on user intent."""
    
    def __init__(self, llm_manager, root_path: Optional[Path] = None):
        self.llm = llm_manager
        self.file_manager = FileContextManager(root_path)
        self.intent_classifier = IntentClassifier(llm_manager)
        self.code_generator = CodeGenerator(llm_manager, self.file_manager)
        self.diff_engine = DiffEngine(self.file_manager)
        self.code_reviewer = CodeReviewer(llm_manager, self.file_manager)
        
        # Pending changes awaiting confirmation
        self._pending_changeset: Optional[ChangeSet] = None
    
    def process(self, message: str, use_llm_classification: bool = True) -> AgentResponse:
        """Process a user message and return appropriate response."""
        # Classify intent
        if use_llm_classification:
            intent = self.intent_classifier.classify_with_llm(message)
        else:
            intent = self.intent_classifier.classify(message)
        
        # Route to appropriate handler
        handlers = {
            IntentType.CODE_GENERATE: self._handle_generate,
            IntentType.CODE_EDIT: self._handle_edit,
            IntentType.CODE_REVIEW: self._handle_review,
            IntentType.CODE_EXPLAIN: self._handle_explain,
            IntentType.CODE_REFACTOR: self._handle_refactor,
            IntentType.TEST_GENERATE: self._handle_test_generate,
            IntentType.FILE_CREATE: self._handle_file_create,
            IntentType.FILE_DELETE: self._handle_file_delete,
            IntentType.PROJECT_INFO: self._handle_project_info,
            IntentType.GENERAL_CHAT: self._handle_general_chat,
        }
        
        handler = handlers.get(intent.type, self._handle_general_chat)
        return handler(message, intent)
    
    def confirm_changes(self) -> Tuple[bool, str]:
        """Apply pending changes after user confirmation."""
        if not self._pending_changeset:
            return False, "No pending changes to apply."
        
        successful, failed = self.diff_engine.apply_changeset(self._pending_changeset)
        self._pending_changeset = None
        
        if failed == 0:
            return True, f"✓ Successfully applied changes to {successful} file(s)."
        else:
            return False, f"Applied {successful} file(s), {failed} failed."
    
    def reject_changes(self) -> str:
        """Reject pending changes."""
        self._pending_changeset = None
        return "Changes discarded."
    
    def _handle_generate(self, message: str, intent: Intent) -> AgentResponse:
        """Handle code generation requests."""
        request = CodeGenerationRequest(
            description=message,
            language=intent.language,
            file_path=intent.file_paths[0] if intent.file_paths else None,
        )
        
        generated = self.code_generator.generate(request)
        
        # Create changeset
        changeset = ChangeSet(description=f"Generate: {message[:50]}...")
        diff = self.diff_engine.create_file_diff(generated.file_path, generated.code)
        changeset.diffs.append(diff)
        
        self._pending_changeset = changeset
        
        # Format response
        preview = self.diff_engine.format_diff_simple(diff)
        
        return AgentResponse(
            message=f"I'll create the following code:\n\n{preview}",
            intent=intent,
            generated_code=generated,
            changeset=changeset,
            requires_confirmation=True,
        )
    
    def _handle_edit(self, message: str, intent: Intent) -> AgentResponse:
        """Handle code editing requests."""
        if not intent.file_paths:
            return AgentResponse(
                message="Please specify which file you want to edit. For example: 'Edit src/main.py to add error handling'",
                intent=intent,
            )
        
        file_path = intent.file_paths[0]
        original = self.file_manager.read_file(file_path)
        
        if not original:
            return AgentResponse(
                message=f"Cannot find file: {file_path}",
                intent=intent,
            )
        
        # Generate edited code
        prompt = f"""Edit the following code according to the user's request.

## Original Code ({file_path})
```
{original[:5000]}
```

## User Request
{message}

## Instructions
1. Make the requested changes
2. Keep the rest of the code unchanged
3. Return the COMPLETE modified file

```
"""
        
        response = self.llm.invoke(prompt)
        new_code = self._extract_code(response)
        
        # Create changeset
        changeset = ChangeSet(description=f"Edit: {message[:50]}...")
        diff = self.diff_engine.create_diff(original, new_code, file_path)
        changeset.diffs.append(diff)
        
        self._pending_changeset = changeset
        
        preview = self.diff_engine.format_diff_simple(diff)
        
        return AgentResponse(
            message=f"Here are the proposed changes:\n\n{preview}",
            intent=intent,
            changeset=changeset,
            requires_confirmation=True,
        )
    
    def _handle_review(self, message: str, intent: Intent) -> AgentResponse:
        """Handle code review requests."""
        if not intent.file_paths:
            # Try to find files to review
            context = self.file_manager.get_project_context()
            py_files = [f.relative_path for f in context.files if f.extension == ".py"][:5]
            
            if py_files:
                return AgentResponse(
                    message=f"Which file would you like me to review? Found these Python files:\n" + 
                           "\n".join(f"  • {f}" for f in py_files),
                    intent=intent,
                )
            return AgentResponse(
                message="Please specify which file you want me to review.",
                intent=intent,
            )
        
        file_path = intent.file_paths[0]
        
        try:
            result = self.code_reviewer.review_file(file_path)
        except ValueError as e:
            return AgentResponse(message=str(e), intent=intent)
        
        # Format review output
        lines = [result.format_summary()]
        
        if result.issues:
            lines.append("Issues found:\n")
            for issue in result.issues[:10]:
                lines.append(issue.format())
                lines.append("")
            
            if len(result.issues) > 10:
                lines.append(f"... and {len(result.issues) - 10} more issues")
        
        return AgentResponse(
            message="\n".join(lines),
            intent=intent,
            review_result=result,
        )
    
    def _handle_explain(self, message: str, intent: Intent) -> AgentResponse:
        """Handle code explanation requests."""
        if not intent.file_paths:
            return AgentResponse(
                message="Please specify which file or code you want me to explain.",
                intent=intent,
            )
        
        file_path = intent.file_paths[0]
        content = self.file_manager.read_file(file_path)
        
        if not content:
            return AgentResponse(
                message=f"Cannot find file: {file_path}",
                intent=intent,
            )
        
        prompt = f"""Explain the following code in a clear, educational way.

## Code ({file_path})
```
{content[:5000]}
```

## Instructions
1. Start with a high-level overview
2. Explain the main components/functions
3. Describe the flow of execution
4. Note any important patterns or techniques used
5. Keep the explanation concise but thorough
"""
        
        explanation = self.llm.invoke(prompt)
        
        return AgentResponse(
            message=f"📖 **Explanation of {file_path}**\n\n{explanation}",
            intent=intent,
        )
    
    def _handle_refactor(self, message: str, intent: Intent) -> AgentResponse:
        """Handle code refactoring requests."""
        if not intent.file_paths:
            return AgentResponse(
                message="Please specify which file you want to refactor.",
                intent=intent,
            )
        
        file_path = intent.file_paths[0]
        original = self.file_manager.read_file(file_path)
        
        if not original:
            return AgentResponse(
                message=f"Cannot find file: {file_path}",
                intent=intent,
            )
        
        prompt = f"""Refactor the following code to improve its quality.

## Original Code ({file_path})
```
{original[:5000]}
```

## User Request
{message}

## Refactoring Goals
1. Improve readability
2. Reduce complexity
3. Follow best practices
4. Improve performance where possible
5. Add/improve documentation

Return the COMPLETE refactored file.

```
"""
        
        response = self.llm.invoke(prompt)
        new_code = self._extract_code(response)
        
        # Create changeset
        changeset = ChangeSet(description=f"Refactor: {file_path}")
        diff = self.diff_engine.create_diff(original, new_code, file_path)
        changeset.diffs.append(diff)
        
        self._pending_changeset = changeset
        
        preview = self.diff_engine.format_diff_simple(diff)
        
        return AgentResponse(
            message=f"Here's the refactored code:\n\n{preview}",
            intent=intent,
            changeset=changeset,
            requires_confirmation=True,
        )
    
    def _handle_test_generate(self, message: str, intent: Intent) -> AgentResponse:
        """Handle test generation requests."""
        if not intent.file_paths:
            return AgentResponse(
                message="Please specify which file you want to generate tests for.",
                intent=intent,
            )
        
        file_path = intent.file_paths[0]
        
        try:
            generated = self.code_generator.generate_test(file_path)
        except ValueError as e:
            return AgentResponse(message=str(e), intent=intent)
        
        # Create changeset
        changeset = ChangeSet(description=f"Generate tests for {file_path}")
        diff = self.diff_engine.create_file_diff(generated.file_path, generated.code)
        changeset.diffs.append(diff)
        
        self._pending_changeset = changeset
        
        preview = self.diff_engine.format_diff_simple(diff)
        
        return AgentResponse(
            message=f"I'll create tests at {generated.file_path}:\n\n{preview}",
            intent=intent,
            generated_code=generated,
            changeset=changeset,
            requires_confirmation=True,
        )
    
    def _handle_file_create(self, message: str, intent: Intent) -> AgentResponse:
        """Handle file creation requests."""
        # Extract file path from message or intent
        file_path = intent.file_paths[0] if intent.file_paths else None
        
        if not file_path:
            return AgentResponse(
                message="Please specify the file path to create.",
                intent=intent,
            )
        
        # Generate initial content based on file type
        request = CodeGenerationRequest(
            description=f"Create a new file: {message}",
            file_path=file_path,
        )
        
        generated = self.code_generator.generate(request)
        
        changeset = ChangeSet(description=f"Create file: {file_path}")
        diff = self.diff_engine.create_file_diff(file_path, generated.code)
        changeset.diffs.append(diff)
        
        self._pending_changeset = changeset
        
        preview = self.diff_engine.format_diff_simple(diff)
        
        return AgentResponse(
            message=f"I'll create {file_path}:\n\n{preview}",
            intent=intent,
            generated_code=generated,
            changeset=changeset,
            requires_confirmation=True,
        )
    
    def _handle_file_delete(self, message: str, intent: Intent) -> AgentResponse:
        """Handle file deletion requests."""
        if not intent.file_paths:
            return AgentResponse(
                message="Please specify which file to delete.",
                intent=intent,
            )
        
        file_path = intent.file_paths[0]
        
        if not self.file_manager.file_exists(file_path):
            return AgentResponse(
                message=f"File not found: {file_path}",
                intent=intent,
            )
        
        content = self.file_manager.read_file(file_path) or ""
        
        changeset = ChangeSet(description=f"Delete file: {file_path}")
        diff = self.diff_engine.create_diff(content, "", file_path)
        changeset.diffs.append(diff)
        
        self._pending_changeset = changeset
        
        return AgentResponse(
            message=f"⚠️ This will delete {file_path} ({len(content)} bytes). Are you sure?",
            intent=intent,
            changeset=changeset,
            requires_confirmation=True,
        )
    
    def _handle_project_info(self, message: str, intent: Intent) -> AgentResponse:
        """Handle project information requests."""
        context = self.file_manager.get_project_context()
        structure = self.file_manager.get_structure_summary(max_depth=3)
        
        info = f"""📁 **Project: {context.root_path.name}**

**Statistics:**
  • Total files: {context.total_files}
  • Code files: {context.total_code_files}
  • Languages: {', '.join(sorted(context.languages)) or 'None detected'}

**Structure:**
{structure}
"""
        
        return AgentResponse(message=info, intent=intent)
    
    def _handle_general_chat(self, message: str, intent: Intent) -> AgentResponse:
        """Handle general chat/questions."""
        # Get project context for better responses
        context = self.file_manager.get_project_context()
        
        prompt = f"""You are a helpful coding assistant. Answer the user's question.

Project context:
- Root: {context.root_path.name}
- Languages: {', '.join(context.languages)}
- Files: {context.total_code_files} code files

User: {message}

Provide a helpful, concise response. If the question is about code, you can suggest using specific commands like:
- "Create a function that..." for code generation
- "Review src/file.py" for code review
- "Explain src/file.py" for explanations
"""
        
        response = self.llm.invoke(prompt)
        
        return AgentResponse(message=response, intent=intent)
    

    def process_stream(self, message: str, use_llm_classification: bool = True) -> Iterator[Tuple[str, Optional[AgentResponse]]]:
        """
        Process a user message with streaming output.
        
        Yields tuples of (chunk, final_response).
        During streaming, final_response is None.
        The last yield will have the complete AgentResponse.
        """
        # Classify intent (non-streaming, it's fast)
        if use_llm_classification:
            intent = self.intent_classifier.classify_with_llm(message)
        else:
            intent = self.intent_classifier.classify(message)
        
        # Route to appropriate streaming handler
        streaming_handlers = {
            IntentType.CODE_GENERATE: self._handle_generate_stream,
            IntentType.CODE_EDIT: self._handle_edit_stream,
            IntentType.CODE_REVIEW: self._handle_review_stream,
            IntentType.CODE_EXPLAIN: self._handle_explain_stream,
            IntentType.CODE_REFACTOR: self._handle_refactor_stream,
            IntentType.GENERAL_CHAT: self._handle_general_chat_stream,
        }
        
        handler = streaming_handlers.get(intent.type)
        
        if handler:
            yield from handler(message, intent)
        else:
            # Fall back to non-streaming for other intents
            response = self.process(message, use_llm_classification)
            yield (response.message, response)
    
    def _handle_explain_stream(self, message: str, intent: Intent) -> Iterator[Tuple[str, Optional[AgentResponse]]]:
        """Handle code explanation with streaming."""
        if not intent.file_paths:
            response = AgentResponse(
                message="Please specify which file or code you want me to explain.",
                intent=intent,
            )
            yield (response.message, response)
            return
        
        file_path = intent.file_paths[0]
        content = self.file_manager.read_file(file_path)
        
        if not content:
            response = AgentResponse(
                message=f"Cannot find file: {file_path}",
                intent=intent,
            )
            yield (response.message, response)
            return
        
        prompt = f"""Explain the following code in a clear, educational way.

## Code ({file_path})
```
{content[:5000]}
```

## Instructions
1. Start with a high-level overview
2. Explain the main components/functions
3. Describe the flow of execution
4. Note any important patterns or techniques used
5. Keep the explanation concise but thorough
"""
        
        # Stream the explanation
        full_response = f"📖 **Explanation of {file_path}**\n\n"
        yield (f"📖 **Explanation of {file_path}**\n\n", None)
        
        for chunk in self.llm.stream(prompt):
            full_response += chunk
            yield (chunk, None)
        
        # Final response
        response = AgentResponse(
            message=full_response,
            intent=intent,
        )
        yield ("", response)
    
    def _handle_review_stream(self, message: str, intent: Intent) -> Iterator[Tuple[str, Optional[AgentResponse]]]:
        """Handle code review with streaming."""
        if not intent.file_paths:
            context = self.file_manager.get_project_context()
            py_files = [f.relative_path for f in context.files if f.extension == ".py"][:5]
            
            if py_files:
                msg = f"Which file would you like me to review? Found these Python files:\n" + \
                      "\n".join(f"  • {f}" for f in py_files)
            else:
                msg = "Please specify which file you want me to review."
            
            response = AgentResponse(message=msg, intent=intent)
            yield (msg, response)
            return
        
        file_path = intent.file_paths[0]
        content = self.file_manager.read_file(file_path)
        
        if not content:
            response = AgentResponse(
                message=f"Cannot find file: {file_path}",
                intent=intent,
            )
            yield (response.message, response)
            return
        
        yield (f"🔍 **Reviewing {file_path}...**\n\n", None)
        
        # Use streaming for the review
        prompt = f"""Review the following code for issues, bugs, and improvements.

## Code ({file_path})
```
{content[:5000]}
```

## Review Format
Provide a structured review with:
1. **Summary** - Brief overview
2. **Issues** - List any bugs, security issues, or problems
3. **Suggestions** - Improvements and best practices
4. **Score** - Rate the code quality (1-10)

Be specific and actionable.
"""
        
        full_response = f"🔍 **Reviewing {file_path}...**\n\n"
        
        for chunk in self.llm.stream(prompt):
            full_response += chunk
            yield (chunk, None)
        
        response = AgentResponse(
            message=full_response,
            intent=intent,
        )
        yield ("", response)
    
    def _handle_generate_stream(self, message: str, intent: Intent) -> Iterator[Tuple[str, Optional[AgentResponse]]]:
        """Handle code generation with streaming."""
        yield ("🔨 **Generating code...**\n\n", None)
        
        request = CodeGenerationRequest(
            description=message,
            language=intent.language,
            file_path=intent.file_paths[0] if intent.file_paths else None,
        )
        
        # Generate code (this part streams)
        full_code = ""
        prompt = self.code_generator._build_prompt(request)
        
        for chunk in self.llm.stream(prompt):
            full_code += chunk
            yield (chunk, None)
        
        # Extract and create changeset
        code = self._extract_code(full_code)
        file_path = request.file_path or f"generated.{request.language or 'py'}"
        
        generated = GeneratedCode(
            code=code,
            language=request.language or "python",
            file_path=file_path,
            description=request.description,
        )
        
        changeset = ChangeSet(description=f"Generate: {message[:50]}...")
        diff = self.diff_engine.create_file_diff(generated.file_path, generated.code)
        changeset.diffs.append(diff)
        
        self._pending_changeset = changeset
        
        response = AgentResponse(
            message=f"\n\n✅ Code generated for {file_path}",
            intent=intent,
            generated_code=generated,
            changeset=changeset,
            requires_confirmation=True,
        )
        yield ("\n\n✅ Code generated. Apply changes? (yes/no)", response)
    
    def _handle_edit_stream(self, message: str, intent: Intent) -> Iterator[Tuple[str, Optional[AgentResponse]]]:
        """Handle code editing with streaming."""
        if not intent.file_paths:
            response = AgentResponse(
                message="Please specify which file you want to edit.",
                intent=intent,
            )
            yield (response.message, response)
            return
        
        file_path = intent.file_paths[0]
        original = self.file_manager.read_file(file_path)
        
        if not original:
            response = AgentResponse(
                message=f"Cannot find file: {file_path}",
                intent=intent,
            )
            yield (response.message, response)
            return
        
        yield (f"✏️ **Editing {file_path}...**\n\n", None)
        
        prompt = f"""Edit the following code according to the user's request.

## Original Code ({file_path})
```
{original[:5000]}
```

## User Request
{message}

## Instructions
Return the COMPLETE modified file.

```
"""
        
        full_response = ""
        for chunk in self.llm.stream(prompt):
            full_response += chunk
            yield (chunk, None)
        
        new_code = self._extract_code(full_response)
        
        changeset = ChangeSet(description=f"Edit: {message[:50]}...")
        diff = self.diff_engine.create_diff(original, new_code, file_path)
        changeset.diffs.append(diff)
        
        self._pending_changeset = changeset
        
        response = AgentResponse(
            message=f"\n\n✅ Edit complete for {file_path}",
            intent=intent,
            changeset=changeset,
            requires_confirmation=True,
        )
        yield ("\n\n✅ Edit complete. Apply changes? (yes/no)", response)
    
    def _handle_refactor_stream(self, message: str, intent: Intent) -> Iterator[Tuple[str, Optional[AgentResponse]]]:
        """Handle code refactoring with streaming."""
        if not intent.file_paths:
            response = AgentResponse(
                message="Please specify which file you want to refactor.",
                intent=intent,
            )
            yield (response.message, response)
            return
        
        file_path = intent.file_paths[0]
        original = self.file_manager.read_file(file_path)
        
        if not original:
            response = AgentResponse(
                message=f"Cannot find file: {file_path}",
                intent=intent,
            )
            yield (response.message, response)
            return
        
        yield (f"🔄 **Refactoring {file_path}...**\n\n", None)
        
        prompt = f"""Refactor the following code to improve its quality.

## Original Code ({file_path})
```
{original[:5000]}
```

## User Request
{message}

Return the COMPLETE refactored file.

```
"""
        
        full_response = ""
        for chunk in self.llm.stream(prompt):
            full_response += chunk
            yield (chunk, None)
        
        new_code = self._extract_code(full_response)
        
        changeset = ChangeSet(description=f"Refactor: {file_path}")
        diff = self.diff_engine.create_diff(original, new_code, file_path)
        changeset.diffs.append(diff)
        
        self._pending_changeset = changeset
        
        response = AgentResponse(
            message=f"\n\n✅ Refactoring complete for {file_path}",
            intent=intent,
            changeset=changeset,
            requires_confirmation=True,
        )
        yield ("\n\n✅ Refactoring complete. Apply changes? (yes/no)", response)
    
    def _handle_general_chat_stream(self, message: str, intent: Intent) -> Iterator[Tuple[str, Optional[AgentResponse]]]:
        """Handle general chat with streaming."""
        context = self.file_manager.get_project_context()
        
        prompt = f"""You are a helpful coding assistant. Answer the user's question.

Project context:
- Root: {context.root_path.name}
- Languages: {', '.join(context.languages)}
- Files: {context.total_code_files} code files

User: {message}

Provide a helpful, concise response.
"""
        
        full_response = ""
        for chunk in self.llm.stream(prompt):
            full_response += chunk
            yield (chunk, None)
        
        response = AgentResponse(message=full_response, intent=intent)
        yield ("", response)



    def process_stream(self, message: str, use_llm_classification: bool = True) -> Iterator[Tuple[str, Optional[AgentResponse]]]:
        """
        Process a user message with streaming output.
        
        Yields tuples of (chunk, final_response).
        During streaming, final_response is None.
        The last yield will have the complete AgentResponse.
        """
        # Classify intent (non-streaming, it's fast)
        if use_llm_classification:
            intent = self.intent_classifier.classify_with_llm(message)
        else:
            intent = self.intent_classifier.classify(message)
        
        # Route to appropriate streaming handler
        streaming_handlers = {
            IntentType.CODE_GENERATE: self._handle_generate_stream,
            IntentType.CODE_EDIT: self._handle_edit_stream,
            IntentType.CODE_REVIEW: self._handle_review_stream,
            IntentType.CODE_EXPLAIN: self._handle_explain_stream,
            IntentType.CODE_REFACTOR: self._handle_refactor_stream,
            IntentType.GENERAL_CHAT: self._handle_general_chat_stream,
        }
        
        handler = streaming_handlers.get(intent.type)
        
        if handler:
            yield from handler(message, intent)
        else:
            # Fall back to non-streaming for other intents
            response = self.process(message, use_llm_classification)
            yield (response.message, response)
    
    def _handle_explain_stream(self, message: str, intent: Intent) -> Iterator[Tuple[str, Optional[AgentResponse]]]:
        """Handle code explanation with streaming."""
        if not intent.file_paths:
            response = AgentResponse(
                message="Please specify which file or code you want me to explain.",
                intent=intent,
            )
            yield (response.message, response)
            return
        
        file_path = intent.file_paths[0]
        content = self.file_manager.read_file(file_path)
        
        if not content:
            response = AgentResponse(
                message=f"Cannot find file: {file_path}",
                intent=intent,
            )
            yield (response.message, response)
            return
        
        prompt = f"""Explain the following code in a clear, educational way.

## Code ({file_path})
```
{content[:5000]}
```

## Instructions
1. Start with a high-level overview
2. Explain the main components/functions
3. Describe the flow of execution
4. Note any important patterns or techniques used
5. Keep the explanation concise but thorough
"""
        
        # Stream the explanation
        full_response = f"📖 **Explanation of {file_path}**\n\n"
        yield (f"📖 **Explanation of {file_path}**\n\n", None)
        
        for chunk in self.llm.stream(prompt):
            full_response += chunk
            yield (chunk, None)
        
        # Final response
        response = AgentResponse(
            message=full_response,
            intent=intent,
        )
        yield ("", response)
    
    def _handle_review_stream(self, message: str, intent: Intent) -> Iterator[Tuple[str, Optional[AgentResponse]]]:
        """Handle code review with streaming."""
        if not intent.file_paths:
            context = self.file_manager.get_project_context()
            py_files = [f.relative_path for f in context.files if f.extension == ".py"][:5]
            
            if py_files:
                msg = f"Which file would you like me to review? Found these Python files:\n" + \
                      "\n".join(f"  • {f}" for f in py_files)
            else:
                msg = "Please specify which file you want me to review."
            
            response = AgentResponse(message=msg, intent=intent)
            yield (msg, response)
            return
        
        file_path = intent.file_paths[0]
        content = self.file_manager.read_file(file_path)
        
        if not content:
            response = AgentResponse(
                message=f"Cannot find file: {file_path}",
                intent=intent,
            )
            yield (response.message, response)
            return
        
        yield (f"🔍 **Reviewing {file_path}...**\n\n", None)
        
        # Use streaming for the review
        prompt = f"""Review the following code for issues, bugs, and improvements.

## Code ({file_path})
```
{content[:5000]}
```

## Review Format
Provide a structured review with:
1. **Summary** - Brief overview
2. **Issues** - List any bugs, security issues, or problems
3. **Suggestions** - Improvements and best practices
4. **Score** - Rate the code quality (1-10)

Be specific and actionable.
"""
        
        full_response = f"🔍 **Reviewing {file_path}...**\n\n"
        
        for chunk in self.llm.stream(prompt):
            full_response += chunk
            yield (chunk, None)
        
        response = AgentResponse(
            message=full_response,
            intent=intent,
        )
        yield ("", response)
    
    def _handle_generate_stream(self, message: str, intent: Intent) -> Iterator[Tuple[str, Optional[AgentResponse]]]:
        """Handle code generation with streaming."""
        yield ("🔨 **Generating code...**\n\n", None)
        
        request = CodeGenerationRequest(
            description=message,
            language=intent.language,
            file_path=intent.file_paths[0] if intent.file_paths else None,
        )
        
        # Generate code (this part streams)
        full_code = ""
        prompt = self.code_generator._build_prompt(request)
        
        for chunk in self.llm.stream(prompt):
            full_code += chunk
            yield (chunk, None)
        
        # Extract and create changeset
        code = self._extract_code(full_code)
        file_path = request.file_path or f"generated.{request.language or 'py'}"
        
        generated = GeneratedCode(
            code=code,
            language=request.language or "python",
            file_path=file_path,
            description=request.description,
        )
        
        changeset = ChangeSet(description=f"Generate: {message[:50]}...")
        diff = self.diff_engine.create_file_diff(generated.file_path, generated.code)
        changeset.diffs.append(diff)
        
        self._pending_changeset = changeset
        
        response = AgentResponse(
            message=f"\n\n✅ Code generated for {file_path}",
            intent=intent,
            generated_code=generated,
            changeset=changeset,
            requires_confirmation=True,
        )
        yield ("\n\n✅ Code generated. Apply changes? (yes/no)", response)
    
    def _handle_edit_stream(self, message: str, intent: Intent) -> Iterator[Tuple[str, Optional[AgentResponse]]]:
        """Handle code editing with streaming."""
        if not intent.file_paths:
            response = AgentResponse(
                message="Please specify which file you want to edit.",
                intent=intent,
            )
            yield (response.message, response)
            return
        
        file_path = intent.file_paths[0]
        original = self.file_manager.read_file(file_path)
        
        if not original:
            response = AgentResponse(
                message=f"Cannot find file: {file_path}",
                intent=intent,
            )
            yield (response.message, response)
            return
        
        yield (f"✏️ **Editing {file_path}...**\n\n", None)
        
        prompt = f"""Edit the following code according to the user's request.

## Original Code ({file_path})
```
{original[:5000]}
```

## User Request
{message}

## Instructions
Return the COMPLETE modified file.

```
"""
        
        full_response = ""
        for chunk in self.llm.stream(prompt):
            full_response += chunk
            yield (chunk, None)
        
        new_code = self._extract_code(full_response)
        
        changeset = ChangeSet(description=f"Edit: {message[:50]}...")
        diff = self.diff_engine.create_diff(original, new_code, file_path)
        changeset.diffs.append(diff)
        
        self._pending_changeset = changeset
        
        response = AgentResponse(
            message=f"\n\n✅ Edit complete for {file_path}",
            intent=intent,
            changeset=changeset,
            requires_confirmation=True,
        )
        yield ("\n\n✅ Edit complete. Apply changes? (yes/no)", response)
    
    def _handle_refactor_stream(self, message: str, intent: Intent) -> Iterator[Tuple[str, Optional[AgentResponse]]]:
        """Handle code refactoring with streaming."""
        if not intent.file_paths:
            response = AgentResponse(
                message="Please specify which file you want to refactor.",
                intent=intent,
            )
            yield (response.message, response)
            return
        
        file_path = intent.file_paths[0]
        original = self.file_manager.read_file(file_path)
        
        if not original:
            response = AgentResponse(
                message=f"Cannot find file: {file_path}",
                intent=intent,
            )
            yield (response.message, response)
            return
        
        yield (f"🔄 **Refactoring {file_path}...**\n\n", None)
        
        prompt = f"""Refactor the following code to improve its quality.

## Original Code ({file_path})
```
{original[:5000]}
```

## User Request
{message}

Return the COMPLETE refactored file.

```
"""
        
        full_response = ""
        for chunk in self.llm.stream(prompt):
            full_response += chunk
            yield (chunk, None)
        
        new_code = self._extract_code(full_response)
        
        changeset = ChangeSet(description=f"Refactor: {file_path}")
        diff = self.diff_engine.create_diff(original, new_code, file_path)
        changeset.diffs.append(diff)
        
        self._pending_changeset = changeset
        
        response = AgentResponse(
            message=f"\n\n✅ Refactoring complete for {file_path}",
            intent=intent,
            changeset=changeset,
            requires_confirmation=True,
        )
        yield ("\n\n✅ Refactoring complete. Apply changes? (yes/no)", response)
    
    def _handle_general_chat_stream(self, message: str, intent: Intent) -> Iterator[Tuple[str, Optional[AgentResponse]]]:
        """Handle general chat with streaming."""
        context = self.file_manager.get_project_context()
        
        prompt = f"""You are a helpful coding assistant. Answer the user's question.

Project context:
- Root: {context.root_path.name}
- Languages: {', '.join(context.languages)}
- Files: {context.total_code_files} code files

User: {message}

Provide a helpful, concise response.
"""
        
        full_response = ""
        for chunk in self.llm.stream(prompt):
            full_response += chunk
            yield (chunk, None)
        
        response = AgentResponse(message=full_response, intent=intent)
        yield ("", response)


    def _extract_code(self, response: str) -> str:
        """Extract code from LLM response."""
        import re
        
        # Try to find code block
        pattern = r"```(?:\w+)?\s*\n(.*?)```"
        match = re.search(pattern, response, re.DOTALL)
        
        if match:
            return match.group(1).strip()
        
        return response.strip()
