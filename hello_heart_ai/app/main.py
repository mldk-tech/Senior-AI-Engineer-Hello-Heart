"""
Main entry point for Hello Heart AI Assistant.

This module provides the main application interface, including
both command-line demo functionality and FastAPI integration.
"""

import logging
import sys
from typing import Dict, Any
from datetime import datetime

from app.orchestration.workflow import HealthAIAssistant
from app.core.config import get_settings, setup_logging


def setup_application():
    """Set up the application with proper logging and configuration."""
    settings = get_settings()
    
    # Set up logging
    setup_logging()
    logger = logging.getLogger("hello_heart.main")
    
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Log level: {settings.log_level}")
    
    return settings, logger


def create_assistant(api_key: str = None) -> HealthAIAssistant:
    """Create and validate the health assistant."""
    try:
        assistant = HealthAIAssistant(openai_api_key=api_key)
        
        # Validate workflow
        if not assistant.validate_workflow():
            logging.error("Workflow validation failed")
            return None
            
        logging.info("Health assistant created successfully")
        return assistant
        
    except Exception as e:
        logging.error(f"Error creating assistant: {e}")
        return None


def demo_health_assistant():
    """Demonstrate all agents working together with test scenarios."""
    settings, logger = setup_application()
    
    # Create assistant
    assistant = create_assistant()
    if not assistant:
        logger.error("Failed to create assistant")
        return
    
    logger.info("=== Hello Heart AI Assistant - Multi-Agent Demo ===\n")
    
    test_scenarios = [
        ("How did I sleep last night?", "Normal health query"),
        ("I'm having chest pain and feel dizzy", "Emergency scenario"),
        ("Should I stop taking my medication?", "Medical advice (requires disclaimer)"),
        ("Am I meeting my activity goals?", "Activity check with follow-up"),
        ("What's my blood pressure trend?", "BP monitoring query")
    ]
    
    for query, scenario in test_scenarios:
        logger.info(f"\nScenario: {scenario}")
        logger.info(f"User: {query}")
        
        try:
            response = assistant.process_message(query)
            logger.info(f"Assistant: {response}")
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            logger.info("Assistant: I'm sorry, I encountered an error.")
        
        logger.info("-" * 50)


def get_system_info() -> Dict[str, Any]:
    """Get comprehensive system information."""
    assistant = create_assistant()
    if not assistant:
        return {"error": "Failed to create assistant"}
    
    return {
        "system_status": assistant.get_system_status(),
        "agent_metrics": assistant.get_agent_metrics(),
        "timestamp": datetime.now().isoformat()
    }


def run_interactive_mode():
    """Run the assistant in interactive mode."""
    settings, logger = setup_application()
    
    assistant = create_assistant()
    if not assistant:
        logger.error("Failed to create assistant")
        return
    
    logger.info("=== Hello Heart AI Assistant - Interactive Mode ===")
    logger.info("Type 'quit' to exit, 'status' for system info, 'help' for commands")
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() == 'quit':
                logger.info("Goodbye!")
                break
            elif user_input.lower() == 'status':
                status = assistant.get_system_status()
                logger.info(f"System Status: {status}")
                continue
            elif user_input.lower() == 'help':
                logger.info("Commands: quit, status, help")
                continue
            elif not user_input:
                continue
            
            response = assistant.process_message(user_input)
            logger.info(f"Assistant: {response}")
            
        except KeyboardInterrupt:
            logger.info("\nGoodbye!")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            logger.info("Assistant: I'm sorry, I encountered an error.")


if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == "demo":
            demo_health_assistant()
        elif mode == "interactive":
            run_interactive_mode()
        elif mode == "status":
            info = get_system_info()
            print(f"System Info: {info}")
        else:
            print("Usage: python main.py [demo|interactive|status]")
            print("  demo: Run demonstration scenarios")
            print("  interactive: Run in interactive mode")
            print("  status: Show system information")
    else:
        # Default to demo mode
        demo_health_assistant() 