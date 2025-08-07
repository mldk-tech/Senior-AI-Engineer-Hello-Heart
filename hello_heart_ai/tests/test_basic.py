"""
Basic tests for Hello Heart AI Assistant.

These tests verify that the core components can be imported
and basic functionality works.
"""

import pytest
from datetime import datetime

# Test imports
def test_imports():
    """Test that all core modules can be imported."""
    try:
        from app.core.config import get_settings, validate_api_key
        from app.models.schemas import HealthAssistantState, Message
        from app.agents.base import BaseHealthAgent
        from app.orchestration.workflow import HealthAIAssistant
        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


def test_settings():
    """Test that settings can be loaded."""
    from app.core.config import get_settings
    
    settings = get_settings()
    assert settings.app_name == "Hello Heart AI Assistant"
    assert settings.app_version == "1.0.0"
    assert isinstance(settings.debug, bool)


def test_health_assistant_creation():
    """Test that HealthAIAssistant can be created."""
    from app.orchestration.workflow import HealthAIAssistant
    
    assistant = HealthAIAssistant()
    assert assistant is not None
    assert hasattr(assistant, 'process_message')


def test_message_creation():
    """Test that Message objects can be created."""
    from app.models.schemas import Message
    
    message = Message(
        role="user",
        content="Hello",
        timestamp=datetime.now().isoformat()
    )
    
    assert message.role == "user"
    assert message.content == "Hello"
    assert message.timestamp is not None


def test_health_assistant_state():
    """Test that HealthAssistantState can be created."""
    from app.models.schemas import HealthAssistantState, Message
    
    state = HealthAssistantState(
        messages=[Message(
            role="user",
            content="Test message",
            timestamp=datetime.now().isoformat()
        )],
        current_intent="HEALTH_QUERY"
    )
    
    assert state.current_intent == "HEALTH_QUERY"
    assert len(state.messages) == 1
    assert state.messages[0].content == "Test message"


def test_basic_message_processing():
    """Test basic message processing functionality."""
    from app.orchestration.workflow import HealthAIAssistant
    
    assistant = HealthAIAssistant()
    
    # Test a simple health query
    response = assistant.process_message("How did I sleep last night?")
    
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0


def test_emergency_detection():
    """Test emergency detection functionality."""
    from app.orchestration.workflow import HealthAIAssistant
    
    assistant = HealthAIAssistant()
    
    # Test emergency detection
    response = assistant.process_message("I'm having chest pain")
    
    assert response is not None
    assert isinstance(response, str)
    # Should contain emergency-related content
    assert any(word in response.lower() for word in ["emergency", "911", "call"])


if __name__ == "__main__":
    # Run basic tests
    test_imports()
    test_settings()
    test_health_assistant_creation()
    test_message_creation()
    test_health_assistant_state()
    test_basic_message_processing()
    test_emergency_detection()
    print("All basic tests passed!") 