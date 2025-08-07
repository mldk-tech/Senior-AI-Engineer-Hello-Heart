"""
Workflow orchestration for Hello Heart AI Assistant.

This module contains the main HealthAIAssistant class that coordinates
all agents using LangGraph for workflow management.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Attempt to import langgraph and related packages
try:
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    from langchain_openai import ChatOpenAI
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    ChatOpenAI = None
    StateGraph = None
    END = None
    MemorySaver = None

from app.models.schemas import HealthAssistantState, Message
from app.core.config import get_settings, validate_api_key
from app.agents.intent import IntentClassificationAgent
from app.agents.data import DataRetrievalAgent
from app.agents.response import ResponseGenerationAgent
from app.agents.safety import SafetyCheckAgent
from app.agents.followup import FollowUpAgent, ProactiveEngagementAgent
from app.agents.rag import FAISSRAGAgent


class HealthAIAssistant:
    """Main orchestrator that coordinates all agents."""

    def __init__(self, openai_api_key: Optional[str] = None):
        self.settings = get_settings()
        
        # Use provided API key or fall back to settings
        if openai_api_key:
            self.settings.openai_api_key = openai_api_key
            
        # Initialize LLM only if a real key is provided and libraries are available
        if LANGGRAPH_AVAILABLE and validate_api_key():
            self.llm = ChatOpenAI(
                api_key=self.settings.openai_api_key,
                model=self.settings.openai_model,
                temperature=self.settings.openai_temperature,
                max_tokens=self.settings.openai_max_tokens,
                top_p=self.settings.openai_top_p
            )
        else:
            self.llm = None
            logging.warning("Using mock LLM - no real API key provided")

        # Set up logging
        self.logger = logging.getLogger("hello_heart.orchestrator")
        self.logger.setLevel(getattr(logging, self.settings.log_level))

        # Initialize agents
        self._initialize_agents()

        # Initialize workflow
        if LANGGRAPH_AVAILABLE:
            self.checkpointer = self._initialize_checkpointer()
            self.workflow = self._build_workflow()
        else:
            self.workflow = None
            self.logger.warning("LangGraph not available - using sequential fallback")

    def _initialize_checkpointer(self):
        """Initialize memory checkpointer for conversation state."""
        # Use memory checkpointer for POC
        memory_checkpointer = MemorySaver()
        self.logger.info("Using memory checkpointer for conversation state")
        return memory_checkpointer

    def _initialize_agents(self):
        """Initialize all specialized agents."""
        self.intent_agent = IntentClassificationAgent(self.llm)
        self.data_agent = DataRetrievalAgent(llm=self.llm)
        self.response_agent = ResponseGenerationAgent(self.llm)
        self.safety_agent = SafetyCheckAgent(self.llm)
        self.followup_agent = FollowUpAgent(self.llm)
        self.proactive_agent = ProactiveEngagementAgent(self.llm)
        self.rag_agent = FAISSRAGAgent(self.llm)

        self.logger.info("All agents initialized successfully")

    def _build_workflow(self) -> Any:
        """Build the LangGraph workflow with all agents."""
        if not LANGGRAPH_AVAILABLE:
            return None

        workflow = StateGraph(HealthAssistantState)
        
        # Create wrapper functions to ensure proper state handling
        def intent_wrapper(state):
            if isinstance(state, dict):
                state = HealthAssistantState(**state)
            return self.intent_agent.process(state)
            
        def rag_wrapper(state):
            if isinstance(state, dict):
                state = HealthAssistantState(**state)
            return self.rag_agent.process(state)
            
        def data_wrapper(state):
            if isinstance(state, dict):
                state = HealthAssistantState(**state)
            return self.data_agent.process(state)
            
        def response_wrapper(state):
            if isinstance(state, dict):
                state = HealthAssistantState(**state)
            return self.response_agent.process(state)
            
        def safety_wrapper(state):
            if isinstance(state, dict):
                state = HealthAssistantState(**state)
            return self.safety_agent.process(state)
            
        def followup_wrapper(state):
            if isinstance(state, dict):
                state = HealthAssistantState(**state)
            return self.followup_agent.process(state)
            
        def proactive_wrapper(state):
            if isinstance(state, dict):
                state = HealthAssistantState(**state)
            return self.proactive_agent.process(state)
        
        # Add nodes with wrappers
        workflow.add_node("intent_classification", intent_wrapper)
        workflow.add_node("rag_retrieval", rag_wrapper)
        workflow.add_node("data_retrieval", data_wrapper)
        workflow.add_node("response_generation", response_wrapper)
        workflow.add_node("safety_check", safety_wrapper)
        workflow.add_node("follow_up_determination", followup_wrapper)
        workflow.add_node("proactive_engagement", proactive_wrapper)

        # Entry point
        workflow.set_entry_point("intent_classification")

        # Enhanced conditional routing after intent classification
        def route_after_intent(state: HealthAssistantState):
            """
            Route to appropriate agent based on intent.
            
            - KNOWLEDGE_QUERY: Route to RAG agent for external knowledge
            - HEALTH_QUERY: Route to data retrieval for personal health data
            - EMERGENCY: Skip to response generation
            - Others: Route to response generation
            """
            # Ensure state is HealthAssistantState object
            if isinstance(state, dict):
                state = HealthAssistantState(**state)
                
            intent = state.current_intent
            
            if intent == "KNOWLEDGE_QUERY":
                return "rag_retrieval"
            elif intent in ["BP_MONITORING", "ACTIVITY_CHECK", "SLEEP_INQUIRY", "HEALTH_QUERY"]:
                return "data_retrieval"
            elif intent == "EMERGENCY":
                return "response_generation"
            else:
                return "response_generation"

        workflow.add_conditional_edges(
            "intent_classification",
            route_after_intent,
            {
                "rag_retrieval": "response_generation",
                "data_retrieval": "response_generation",
                "response_generation": "response_generation"
            }
        )

        # Normal flow
        workflow.add_edge("response_generation", "safety_check")
        workflow.add_edge("safety_check", "follow_up_determination")
        workflow.add_edge("follow_up_determination", "proactive_engagement")
        
        # End
        workflow.add_edge("proactive_engagement", END)

        compiled_workflow = workflow.compile(checkpointer=self.checkpointer)
        self.logger.info("LangGraph workflow built successfully with RAG integration")
        return compiled_workflow

    def process_message(self, user_message: str, thread_id: str = "default") -> str:
        """Process a user message through all agents."""
        try:
            self.logger.info(f"Processing message: {user_message[:50]}...")

            # Create initial state
            initial_state = HealthAssistantState(
                messages=[Message(
                    role="user",
                    content=user_message,
                    timestamp=datetime.now().isoformat()
                )],
                user_health_data={},
                current_intent="",
                requires_medical_disclaimer=False,
                conversation_phase="assessment",
                follow_up_needed=False,
                safety_flags=[],
                proactive_nudge=None
            )

            # Process through workflow
            if LANGGRAPH_AVAILABLE and self.workflow:
                config = {"configurable": {"thread_id": thread_id}}
                final_state = self.workflow.invoke(initial_state, config)
                
                # Ensure final_state is a HealthAssistantState object
                if isinstance(final_state, dict):
                    final_state = HealthAssistantState(**final_state)
            else:
                # Fallback sequential execution
                final_state = self._process_sequentially(initial_state)

            # Extract the assistant's final response
            if final_state.messages:
                response = final_state.messages[-1].content
            else:
                response = "I'm sorry, I couldn't process your message."

            # Log processing results
            self.logger.info(f"Processing completed. Intent: {final_state.current_intent}")
            self.logger.info(f"Safety flags: {final_state.safety_flags}")
            self.logger.info(f"Follow-up needed: {final_state.follow_up_needed}")

            return response

        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return "I'm sorry, I encountered an error while processing your message. Please try again."

    def _process_sequentially(self, state: HealthAssistantState) -> HealthAssistantState:
        """Process state through agents sequentially (fallback)."""
        try:
            # Intent classification
            state = self.intent_agent.process(state)
            
            # Route based on intent (similar to workflow logic)
            if state.current_intent == "KNOWLEDGE_QUERY":
                # RAG retrieval for knowledge queries
                state = self.rag_agent.process(state)
            elif state.current_intent in ["BP_MONITORING", "ACTIVITY_CHECK", "SLEEP_INQUIRY", "HEALTH_QUERY"]:
                # Data retrieval for personal health queries
                state = self.data_agent.process(state)
            elif state.current_intent == "EMERGENCY":
                # Skip data retrieval for emergencies
                pass
            # For other intents, proceed directly to response generation
            
            # Response generation
            state = self.response_agent.process(state)
            
            # Safety check
            state = self.safety_agent.process(state)
            
            # Follow-up determination
            state = self.followup_agent.process(state)
            
            # Proactive engagement
            state = self.proactive_agent.process(state)
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error in sequential processing: {e}")
            return state

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            "app_name": self.settings.app_name,
            "app_version": self.settings.app_version,
            "langgraph_available": LANGGRAPH_AVAILABLE,
            "llm_configured": self.llm is not None,
            "api_key_valid": validate_api_key(),
            "agents": {
                "intent": self.intent_agent.get_agent_info(),
                "data": self.data_agent.get_agent_info(),
                "response": self.response_agent.get_agent_info(),
                "safety": self.safety_agent.get_agent_info(),
                "followup": self.followup_agent.get_agent_info(),
                "proactive": self.proactive_agent.get_agent_info(),
                "rag": self.rag_agent.get_agent_info()
            },
            "settings": {
                "debug": self.settings.debug,
                "log_level": self.settings.log_level,
                "safety_checks_enabled": self.settings.enable_safety_checks,
                "emergency_escalation_enabled": self.settings.emergency_escalation_enabled
            },
            "timestamp": datetime.now().isoformat()
        }

    def get_agent_metrics(self) -> Dict[str, Any]:
        """Get metrics from all agents."""
        return {
            "intent_confidence": self.intent_agent.get_intent_confidence("test message"),
            "data_summary": self.data_agent.get_data_summary("HEALTH_QUERY"),
            "response_metrics": self.response_agent.get_response_metrics("test response"),
            "safety_metrics": self.safety_agent.get_safety_metrics("test content"),
            "follow_up_metrics": self.followup_agent.get_follow_up_metrics({}),
            "engagement_metrics": self.proactive_agent.get_engagement_metrics(HealthAssistantState())
        }

    def validate_workflow(self) -> bool:
        """Validate that the workflow is properly configured."""
        try:
            # Check if all agents are initialized
            agents = [
                self.intent_agent, self.data_agent, self.response_agent,
                self.safety_agent, self.followup_agent, self.proactive_agent,
                self.rag_agent
            ]
            
            for agent in agents:
                if not agent:
                    self.logger.error(f"Agent not initialized: {agent}")
                    return False
            
            # Check if workflow is available
            if not self.workflow and LANGGRAPH_AVAILABLE:
                self.logger.error("Workflow not built despite LangGraph being available")
                return False
                
            self.logger.info("Workflow validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Workflow validation failed: {e}")
            return False 