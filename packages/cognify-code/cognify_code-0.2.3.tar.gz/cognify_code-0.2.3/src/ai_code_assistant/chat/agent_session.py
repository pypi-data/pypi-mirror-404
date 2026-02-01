"""Agent-enhanced chat session with code generation and review capabilities."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Literal, Optional

from ai_code_assistant.config import Config
from ai_code_assistant.llm import LLMManager
from ai_code_assistant.agent import CodeAgent, AgentResponse, IntentType


@dataclass
class AgentMessage:
    """A message in the agent chat session."""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    response: Optional[AgentResponse] = None
    pending_action: bool = False


class AgentChatSession:
    """Chat session enhanced with code agent capabilities."""
    
    def __init__(
        self,
        config: Config,
        llm_manager: LLMManager,
        root_path: Optional[Path] = None,
    ):
        self.config = config
        self.llm = llm_manager
        self.agent = CodeAgent(llm_manager, root_path or Path.cwd())
        self.history: List[AgentMessage] = []
        self._awaiting_confirmation = False
    
    @property
    def has_pending_changes(self) -> bool:
        """Check if there are pending changes awaiting confirmation."""
        return self._awaiting_confirmation
    
    def send_message(self, user_input: str) -> AgentMessage:
        """Process user message through the agent."""
        # Add user message to history
        user_msg = AgentMessage(role="user", content=user_input)
        self.history.append(user_msg)
        
        # Check for confirmation/rejection of pending changes
        if self._awaiting_confirmation:
            return self._handle_confirmation(user_input)
        
        # Process through agent
        response = self.agent.process(user_input)
        
        # Create assistant message
        assistant_msg = AgentMessage(
            role="assistant",
            content=response.message,
            response=response,
            pending_action=response.requires_confirmation,
        )
        self.history.append(assistant_msg)
        
        # Track if we're awaiting confirmation
        self._awaiting_confirmation = response.requires_confirmation
        
        return assistant_msg
    
    def _handle_confirmation(self, user_input: str) -> AgentMessage:
        """Handle user confirmation or rejection of pending changes."""
        lower_input = user_input.lower().strip()
        
        # Check for confirmation
        if lower_input in ("yes", "y", "confirm", "apply", "ok", "sure", "do it"):
            success, message = self.agent.confirm_changes()
            self._awaiting_confirmation = False
            
            return AgentMessage(
                role="assistant",
                content=message,
            )
        
        # Check for rejection
        elif lower_input in ("no", "n", "cancel", "reject", "discard", "nevermind"):
            message = self.agent.reject_changes()
            self._awaiting_confirmation = False
            
            return AgentMessage(
                role="assistant",
                content=message,
            )
        
        # Unclear response
        else:
            return AgentMessage(
                role="assistant",
                content="Please confirm with 'yes' to apply changes or 'no' to discard them.",
                pending_action=True,
            )
    
    def confirm_changes(self) -> str:
        """Programmatically confirm pending changes."""
        if not self._awaiting_confirmation:
            return "No pending changes."
        
        success, message = self.agent.confirm_changes()
        self._awaiting_confirmation = False
        return message
    
    def reject_changes(self) -> str:
        """Programmatically reject pending changes."""
        if not self._awaiting_confirmation:
            return "No pending changes."
        
        message = self.agent.reject_changes()
        self._awaiting_confirmation = False
        return message
    
    def get_project_info(self) -> str:
        """Get information about the current project."""
        response = self.agent.process("show project info")
        return response.message
    
    def review_file(self, file_path: str) -> AgentMessage:
        """Review a specific file."""
        return self.send_message(f"review {file_path}")
    
    def generate_code(self, description: str, file_path: Optional[str] = None) -> AgentMessage:
        """Generate code based on description."""
        if file_path:
            return self.send_message(f"create {file_path}: {description}")
        return self.send_message(f"generate code: {description}")
    
    def explain_file(self, file_path: str) -> AgentMessage:
        """Explain a file's code."""
        return self.send_message(f"explain {file_path}")
    
    def get_history(self) -> List[AgentMessage]:
        """Get conversation history."""
        return self.history.copy()
    
    def clear_history(self) -> None:
        """Clear conversation history."""
        self.history.clear()
        self._awaiting_confirmation = False
    
    def format_response(self, msg: AgentMessage) -> str:
        """Format a message for display."""
        lines = [msg.content]
        
        if msg.pending_action:
            lines.append("")
            lines.append("[yellow]Apply these changes? (yes/no)[/yellow]")
        
        return "\n".join(lines)
