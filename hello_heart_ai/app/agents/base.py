"""
Base agent class for Hello Heart AI Assistant.

This module provides the foundation for all specialized agents
with common functionality like logging, error handling, and
LLM integration.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

from app.models.schemas import HealthAssistantState, AgentResponse
from app.core.config import get_settings


class BaseHealthAgent(ABC):
    """Base class for all health agents with common functionality."""

    def __init__(self, llm: Optional[Any] = None):
        self.llm = llm
        self.agent_name = self.__class__.__name__
        self.settings = get_settings()
        
        # Set up logging
        self.logger = logging.getLogger(f"hello_heart.{self.agent_name}")
        self.logger.setLevel(getattr(logging, self.settings.log_level))

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        pass

    @abstractmethod
    def process(self, state: HealthAssistantState) -> HealthAssistantState:
        """Process the state and return updated state."""
        pass

    def create_prompt(self, context: Dict[str, Any]) -> str:
        """Create a full prompt with system instructions and context."""
        try:
            context_str = json.dumps(context, indent=2, default=str)
            return f"{self.get_system_prompt()}\n\nContext:\n{context_str}"
        except Exception as e:
            self.logger.error(f"Error creating prompt: {e}")
            return self.get_system_prompt()

    def log_processing_start(self, state: HealthAssistantState) -> None:
        """Log the start of agent processing."""
        self.logger.info(
            f"Starting {self.agent_name} processing for intent: {state.current_intent}"
        )

    def log_processing_end(self, state: HealthAssistantState) -> None:
        """Log the end of agent processing."""
        self.logger.info(
            f"Completed {self.agent_name} processing. "
            f"Safety flags: {state.safety_flags}, "
            f"Follow-up needed: {state.follow_up_needed}"
        )

    def handle_error(self, error: Exception, state: HealthAssistantState) -> HealthAssistantState:
        """Handle errors during agent processing."""
        self.logger.error(f"Error in {self.agent_name}: {error}")
        
        # Add error message to state
        error_message = f"An error occurred while processing your request. Please try again."
        state.messages.append({
            "role": "assistant",
            "content": error_message,
            "timestamp": datetime.now().isoformat(),
            "priority": "error"
        })
        
        return state

    def validate_state(self, state: HealthAssistantState) -> bool:
        """Validate the input state."""
        try:
            # Basic validation - ensure required fields exist
            if not hasattr(state, 'messages') or not state.messages:
                self.logger.warning("State missing messages")
                return False
            
            if not hasattr(state, 'current_intent'):
                self.logger.warning("State missing current_intent")
                return False
                
            return True
        except Exception as e:
            self.logger.error(f"State validation error: {e}")
            return False

    def create_response(self, success: bool, message: str, 
                       data: Optional[Dict[str, Any]] = None,
                       safety_flags: Optional[list] = None) -> AgentResponse:
        """Create a standardized agent response."""
        return AgentResponse(
            success=success,
            message=message,
            data=data,
            safety_flags=safety_flags or []
        )

    def should_process(self, state: HealthAssistantState) -> bool:
        """Determine if this agent should process the current state."""
        # Override in subclasses for specific logic
        return True

    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about this agent."""
        return {
            "name": self.agent_name,
            "description": self.__doc__ or "No description available",
            "has_llm": self.llm is not None,
            "settings": {
                "debug": self.settings.debug,
                "log_level": self.settings.log_level
            }
        } 