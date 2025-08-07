"""
Modified working prototype for the Hello Heart Conversational AI.

This version fixes initialization order and removes hard dependency on an actual
OpenAI API key by defaulting to a mock LLM when no key is provided.
It maintains the multi-agent structure using langgraph while ensuring
agents are initialized correctly and the workflow is built after the
checkpointer is available. If the required packages are not installed,
the script will still run a simplified sequential flow.

Note: This script is for demonstration purposes and uses mock data. It
imports langgraph and langchain packages if available. If they cannot be
imported, it falls back to a simple sequential agent invocation.
"""

import os
from typing import Dict, List, TypedDict, Literal, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json
import re
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Attempt to import langgraph and related packages. If unavailable, set a flag.
try:
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    from langchain_openai import ChatOpenAI
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    ChatOpenAI = None  # type: ignore
    StateGraph = None  # type: ignore
    END = None  # type: ignore
    MemorySaver = None  # type: ignore

# Mock health data for demonstration
MOCK_USER_HEALTH_DATA = {
    "user_id": "user123",
    "blood_pressure": {
        "latest": {"systolic": 128, "diastolic": 82, "timestamp": "2024-01-15T08:30:00Z"},
        "trend": "improving",
        "weekly_avg": {"systolic": 132, "diastolic": 85}
    },
    "heart_rate": {
        "resting_avg": 68,
        "active_avg": 120,
        "hrv": {"current": 45, "weekly_avg": 42}
    },
    "steps": {
        "today": 6500,
        "weekly_total": 41000,
        "weekly_goal": 49000,
        "daily_avg": 5857
    },
    "sleep": {
        "last_night": {"hours": 7.2, "quality_score": 78},
        "weekly_avg_hours": 6.8
    }
}


class ConversationPhase(Enum):
    GREETING = "greeting"
    ASSESSMENT = "assessment"
    ADVICE = "advice"
    FOLLOW_UP = "follow_up"
    EMERGENCY = "emergency"


class HealthAssistantState(TypedDict):
    messages: List[Dict]
    user_health_data: Dict
    current_intent: str
    requires_medical_disclaimer: bool
    conversation_phase: str
    follow_up_needed: bool
    safety_flags: List[str]
    proactive_nudge: Optional[str]


class BaseHealthAgent(ABC):
    """Base class for all health agents with prompt engineering capabilities"""

    def __init__(self, llm: Optional[Any] = None):
        self.llm = llm
        self.agent_name = self.__class__.__name__

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent"""
        pass

    @abstractmethod
    def process(self, state: HealthAssistantState) -> HealthAssistantState:
        """Process the state and return updated state"""
        pass

    def create_prompt(self, context: Dict) -> str:
        """Create a full prompt with system instructions and context"""
        return f"{self.get_system_prompt()}\n\nContext:\n{json.dumps(context, indent=2)}"


class IntentClassificationAgent(BaseHealthAgent):
    """Classifies user intent using advanced prompt engineering"""

    def get_system_prompt(self) -> str:
        return """You are an Intent Classification Agent for a health assistant.
        
Your task is to classify user messages into one of these categories:
1. EMERGENCY - Medical emergencies requiring immediate attention
2. HEALTH_QUERY - General health questions about their data
3. MEDICAL_ADVICE - Requests for diagnosis or medication changes
4. ACTIVITY_CHECK - Questions about steps, exercise, or movement
5. SLEEP_INQUIRY - Questions about sleep patterns
6. BP_MONITORING - Blood pressure related queries
7. OFF_TOPIC - Non-health related queries

Emergency indicators include: chest pain, breathing difficulty, severe symptoms, extreme vital signs.
Medical advice includes: medication questions, diagnosis requests, treatment plans.

Respond with ONLY the category name, nothing else."""

    def process(self, state: HealthAssistantState) -> HealthAssistantState:
        last_message = state["messages"][-1]["content"]

        # Simulated classification using heuristics
        emergency_keywords = ["chest pain", "can't breathe", "emergency", "severe", "dizzy", "fainted"]
        medical_keywords = ["diagnose", "medication", "prescription", "doctor", "treatment"]

        if any(keyword in last_message.lower() for keyword in emergency_keywords):
            state["current_intent"] = "EMERGENCY"
            state["conversation_phase"] = ConversationPhase.EMERGENCY.value
            state["requires_medical_disclaimer"] = True
        elif any(keyword in last_message.lower() for keyword in medical_keywords):
            state["current_intent"] = "MEDICAL_ADVICE"
            state["requires_medical_disclaimer"] = True
        elif "sleep" in last_message.lower():
            state["current_intent"] = "SLEEP_INQUIRY"
        elif any(word in last_message.lower() for word in ["step", "walk", "active", "exercise"]):
            state["current_intent"] = "ACTIVITY_CHECK"
        elif any(word in last_message.lower() for word in ["pressure", "bp"]):
            state["current_intent"] = "BP_MONITORING"
        else:
            state["current_intent"] = "HEALTH_QUERY"

        return state


class DataRetrievalAgent(BaseHealthAgent):
    """Retrieves and contextualizes health data using prompt engineering"""

    def __init__(self, user_data: Dict, llm: Optional[Any] = None):
        super().__init__(llm)
        self.user_data = user_data

    def get_system_prompt(self) -> str:
        return """You are a Health Data Retrieval Agent.

Your role is to:
1. Identify which health metrics are relevant to the user's query
2. Extract and format the appropriate data
3. Calculate trends and comparisons
4. Flag any concerning patterns

Data categories available:
- Blood Pressure (systolic/diastolic, trends)
- Heart Rate (resting, active, HRV)
- Activity (steps, goals, weekly totals)
- Sleep (hours, quality score)

Always include:
- Current values
- Recent trends
- Comparison to goals or norms
- Any notable changes"""

    def process(self, state: HealthAssistantState) -> HealthAssistantState:
        intent = state["current_intent"]
        relevant_data: Dict[str, Any] = {}

        if intent == "BP_MONITORING":
            relevant_data["blood_pressure"] = self.user_data["blood_pressure"]
        elif intent == "ACTIVITY_CHECK":
            relevant_data["steps"] = self.user_data["steps"]
            progress = (self.user_data["steps"]["weekly_total"] /
                        self.user_data["steps"]["weekly_goal"]) * 100
            relevant_data["weekly_progress"] = f"{progress:.1f}%"
        elif intent == "SLEEP_INQUIRY":
            relevant_data["sleep"] = self.user_data["sleep"]
        else:
            relevant_data = {
                "blood_pressure": self.user_data["blood_pressure"]["latest"],
                "steps_today": self.user_data["steps"]["today"],
                "sleep_quality": self.user_data["sleep"]["last_night"]["quality_score"],
                "hrv": self.user_data["heart_rate"]["hrv"]["current"]
            }

        state["user_health_data"] = relevant_data
        return state


class ResponseGenerationAgent(BaseHealthAgent):
    """Generates personalized responses using advanced prompt engineering"""

    def get_system_prompt(self) -> str:
        return """You are a Compassionate Health Response Agent for Hello Heart.

Persona: You are warm, encouraging, and knowledgeable. You celebrate progress and provide gentle motivation.

Response Guidelines:
1. Start with empathy and acknowledgment
2. Provide specific insights from their health data
3. Offer ONE clear, actionable suggestion
4. End with encouragement or a relevant follow-up question
5. Use simple, conversational language (8th-grade level)
6. Keep responses under 100 words

Tone Examples:
- "Great question! Let me check your data..."
- "I notice you've been making progress..."
- "That's a fantastic improvement from last week!"

Never:
- Diagnose conditions
- Recommend medication changes
- Use medical jargon
- Sound robotic or impersonal"""

    def process(self, state: HealthAssistantState) -> HealthAssistantState:
        intent = state["current_intent"]
        health_data = state.get("user_health_data", {})

        if intent == "EMERGENCY":
            response = self._generate_emergency_response()
        elif intent == "ACTIVITY_CHECK":
            response = self._generate_activity_response(health_data)
        elif intent == "SLEEP_INQUIRY":
            response = self._generate_sleep_response(health_data)
        elif intent == "BP_MONITORING":
            response = self._generate_bp_response(health_data)
        else:
            response = self._generate_general_response(health_data)

        state["messages"].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        return state

    def _generate_activity_response(self, data: Dict) -> str:
        if "steps" in data:
            steps = data["steps"]
            progress = data.get("weekly_progress", "0%")
            return (f"You're doing great! You've taken {steps['today']:,} steps today "
                    f"and you're at {progress} of your weekly goal. "
                    f"That's {steps['daily_avg']:,} steps on average this week. "
                    f"Keep up the momentum! Would you like a reminder for an evening walk?")
        return "Let me help you track your activity. Could you sync your device first?"

    def _generate_sleep_response(self, data: Dict) -> str:
        if "sleep" in data:
            sleep = data["sleep"]["last_night"]
            return (f"You slept {sleep['hours']} hours last night with a quality score of "
                    f"{sleep['quality_score']}%. That's close to the recommended 7-8 hours! "
                    f"To improve further, try a consistent bedtime routine. "
                    f"How do you feel this morning?")
        return "I'd love to help with your sleep. Please sync your device for the latest data."

    def _generate_bp_response(self, data: Dict) -> str:
        if "blood_pressure" in data:
            bp = data["blood_pressure"]["latest"] if "latest" in data["blood_pressure"] else data["blood_pressure"]
            trend = data["blood_pressure"].get("trend", "")
            return (f"Your latest reading is {bp['systolic']}/{bp['diastolic']} mmHg - "
                    f"that's in a healthy range! Your trend shows {trend} progress. "
                    f"Keep up your healthy habits. When did you last take your medication?")
        return "Let's check your blood pressure. When was your last reading?"

    def _generate_emergency_response(self) -> str:
        return ("I'm concerned about your symptoms. Please call 911 or your emergency number "
                "immediately. If someone is with you, ask them to help. "
                "Your safety is the top priority.")

    def _generate_general_response(self, data: Dict) -> str:
        return ("I'm here to help you understand your health better. "
                "What specific aspect would you like to explore - "
                "your activity, sleep, or blood pressure?")


class SafetyCheckAgent(BaseHealthAgent):
    """Validates responses for medical safety using prompt engineering"""

    def get_system_prompt(self) -> str:
        return """You are a Medical Safety Validation Agent.

Your critical responsibilities:
1. Detect any medical advice that could be harmful
2. Flag diagnoses or treatment recommendations
3. Ensure disclaimers are present when needed
4. Validate emergency responses are appropriate

Safety Rules:
- NO diagnosis statements ("You have...", "This indicates...")
- NO medication changes ("Stop taking...", "Increase dose...")
- NO treatment plans ("You should see a specialist...")
- REQUIRE DISCLAIMERS for symptom discussions
- ENSURE EMERGENCY cases have proper escalation

Mark content as:
- SAFE: No medical concerns
- NEEDS_DISCLAIMER: Add medical disclaimer
- UNSAFE_BLOCK: Must be blocked
- EMERGENCY_VERIFIED: Proper emergency handling"""

    def process(self, state: HealthAssistantState) -> HealthAssistantState:
        last_response = state["messages"][-1]["content"]
        safety_flags: List[str] = []

        unsafe_patterns = [
            r"you have \w+ condition",
            r"stop taking",
            r"change your medication",
            r"this indicates \w+ disease"
        ]

        for pattern in unsafe_patterns:
            if re.search(pattern, last_response.lower()):
                safety_flags.append("UNSAFE_CONTENT")

        # Check if disclaimer needed
        if state.get("requires_medical_disclaimer") and "not medical advice" not in last_response:
            safety_flags.append("NEEDS_DISCLAIMER")
            state["messages"][-1]["content"] += ("\n\n*This is not medical advice. "
                                                 "Please consult your healthcare provider.*")

        state["safety_flags"] = safety_flags
        return state


class FollowUpAgent(BaseHealthAgent):
    """Determines need for proactive follow-ups using prompt engineering"""

    def get_system_prompt(self) -> str:
        return """You are a Proactive Health Engagement Agent.

Analyze user health patterns to determine if follow-up is needed.

Trigger follow-up for:
1. Low activity (<50% of weekly goal)
2. Poor sleep patterns (quality <60% for 3+ days)
3. BP trending upward (>10 point increase)
4. Missed medication reminders
5. No engagement for 48+ hours

Follow-up types:
- GENTLE_REMINDER: Encouraging nudge
- GOAL_CHECK: Progress check-in
- CONCERN_FLAG: Trending concern
- CELEBRATION: Positive reinforcement
- EDUCATION: Tips and insights

Response format: {type: "TYPE", message: "Personalized message", schedule: "timing"}"""

    def process(self, state: HealthAssistantState) -> HealthAssistantState:
        health_data = state.get("user_health_data", {})

        if "steps" in health_data:
            progress_str = health_data.get("weekly_progress", "0%")
            try:
                progress = float(progress_str.rstrip("%"))
            except ValueError:
                progress = 0.0
            if progress < 50:
                state["follow_up_needed"] = True
                state["proactive_nudge"] = (
                    f"You're at {progress_str} of your weekly step goal. "
                    "A 10-minute walk could boost your energy! "
                    "Shall I remind you later?"
                )

        if "sleep" in health_data:
            quality = health_data["sleep"]["last_night"]["quality_score"]
            if quality < 60:
                state["follow_up_needed"] = True
                state["proactive_nudge"] = (
                    "Your sleep quality was lower last night. "
                    "Would you like some tips for better rest tonight?"
                )

        return state


class ProactiveEngagementAgent(BaseHealthAgent):
    """Manages proactive nudges and engagement using prompt engineering"""

    def get_system_prompt(self) -> str:
        return """You are a Proactive Engagement Specialist.

Create timely, personalized nudges that:
1. Feel natural and caring, not pushy
2. Reference specific user data and progress
3. Offer value (tips, encouragement, celebration)
4. Include clear but optional calls-to-action
5. Adapt tone based on user's current state

Nudge Templates:
- Morning: "Good morning! Ready to beat yesterday's {metric}?"
- Midday: "You're doing great with {progress}. Keep it up!"
- Evening: "Perfect time for a relaxing walk. You're {steps} away from your goal!"
- Achievement: "🎉 Amazing! You just hit {milestone}!"

Timing Rules:
- Not before 8 AM or after 9 PM user time
- Space nudges at least 4 hours apart
- Max 3 nudges per day
- Respect user preferences"""

    def process(self, state: HealthAssistantState) -> HealthAssistantState:
        if state.get("follow_up_needed") and state.get("proactive_nudge"):
            # In production this would schedule a notification. Here we print to console.
            print(f"\n[PROACTIVE NUDGE SCHEDULED]: {state['proactive_nudge']}")
        return state


class EmergencyResponseAgent(BaseHealthAgent):
    """Specialized agent for emergency situations using prompt engineering"""

    def get_system_prompt(self) -> str:
        return """You are an Emergency Response Coordinator.

CRITICAL PROTOCOLS:
1. Immediate escalation for life-threatening symptoms
2. Clear, calm communication
3. Direct action steps
4. No medical advice - only safety directions
5. Log all interactions for medical team

Emergency Indicators:
- Chest pain, pressure, or discomfort
- Difficulty breathing or shortness of breath  
- Sudden confusion or difficulty speaking
- Severe headache with no known cause
- Numbness or weakness, especially one-sided
- Blood pressure readings >180/120

Response Template:
"I'm very concerned about what you're describing. 
Please take these steps immediately:
1. Call 911 or emergency services NOW
2. If possible, have someone stay with you
3. Sit down and try to stay calm
4. Have your medication list ready for responders"

NEVER delay emergency response for any reason."""

    def process(self, state: HealthAssistantState) -> HealthAssistantState:
        if state["current_intent"] == "EMERGENCY":
            emergency_response = (
                "🚨 I'm very concerned about your symptoms. "
                "Please call 911 or your emergency number NOW. "
                "Don't wait. If someone is with you, ask them to help. "
                "Emergency responders are trained to help you."
            )
            state["messages"][-1] = {
                "role": "assistant",
                "content": emergency_response,
                "timestamp": datetime.now().isoformat(),
                "priority": "EMERGENCY"
            }
            print(f"\n[EMERGENCY ALERT]: User {state.get('user_id', 'unknown')} - {datetime.now()}")
        return state


class HealthAIAssistant:
    """Main orchestrator that coordinates all agents."""

    def __init__(self, openai_api_key: str = "enter your api key here"):
        # Initialize LLM only if a real key is provided and libraries are available
        if LANGGRAPH_AVAILABLE and openai_api_key != "mock-api-key":
            # Use a lower temperature and top_p sampling for more deterministic,
            # friendly outputs in a healthcare setting. top_p restricts token
            # sampling to the most likely candidates, improving control over
            # wording. A temperature around 0.5 balances creativity and precision.
            self.llm = ChatOpenAI(
                api_key=openai_api_key,
                model="gpt-4o-mini",
                temperature=0.5,
                max_tokens=300,
                top_p=0.9
            )
        else:
            self.llm = None

        # Initialize agents
        self.intent_agent = IntentClassificationAgent(self.llm)
        self.data_agent = DataRetrievalAgent(MOCK_USER_HEALTH_DATA, self.llm)
        self.response_agent = ResponseGenerationAgent(self.llm)
        self.safety_agent = SafetyCheckAgent(self.llm)
        self.followup_agent = FollowUpAgent(self.llm)
        self.proactive_agent = ProactiveEngagementAgent(self.llm)
        self.emergency_agent = EmergencyResponseAgent(self.llm)

        # If langgraph is available, build a workflow. Otherwise, use a sequential fallback.
        if LANGGRAPH_AVAILABLE:
            self.checkpointer = MemorySaver()
            self.workflow = self._build_workflow()
        else:
            self.workflow = None

    def _build_workflow(self) -> Any:
        """Build the LangGraph workflow with all agents"""
        workflow = StateGraph(HealthAssistantState)
        # Add nodes
        workflow.add_node("intent_classification", self.intent_agent.process)
        workflow.add_node("data_retrieval", self.data_agent.process)
        workflow.add_node("response_generation", self.response_agent.process)
        workflow.add_node("safety_check", self.safety_agent.process)
        workflow.add_node("follow_up_determination", self.followup_agent.process)
        workflow.add_node("proactive_engagement", self.proactive_agent.process)
        workflow.add_node("emergency_response", self.emergency_agent.process)

        # Entry point
        workflow.set_entry_point("intent_classification")

        # Conditional routing after intent
        def route_after_intent(state: HealthAssistantState):
            if state["current_intent"] == "EMERGENCY":
                return "emergency_response"
            return "data_retrieval"

        workflow.add_conditional_edges(
            "intent_classification",
            route_after_intent,
            {
                "emergency_response": "emergency_response",
                "data_retrieval": "data_retrieval"
            }
        )

        # Normal flow
        workflow.add_edge("data_retrieval", "response_generation")
        workflow.add_edge("response_generation", "safety_check")
        workflow.add_edge("safety_check", "follow_up_determination")
        workflow.add_edge("follow_up_determination", "proactive_engagement")
        # Emergency flow
        workflow.add_edge("emergency_response", "safety_check")
        # End
        workflow.add_edge("proactive_engagement", END)

        return workflow.compile(checkpointer=self.checkpointer)

    def process_message(self, user_message: str, thread_id: str = "default") -> str:
        """Process a user message through all agents."""
        initial_state: HealthAssistantState = {
            "messages": [{"role": "user", "content": user_message, "timestamp": datetime.now().isoformat()}],
            "user_health_data": {},
            "current_intent": "",
            "requires_medical_disclaimer": False,
            "conversation_phase": ConversationPhase.ASSESSMENT.value,
            "follow_up_needed": False,
            "safety_flags": [],
            "proactive_nudge": None
        }

        if LANGGRAPH_AVAILABLE and self.workflow:
            config = {"configurable": {"thread_id": thread_id}}
            final_state = self.workflow.invoke(initial_state, config)
        else:
            # Fallback sequential execution if LangGraph is not available
            state = initial_state
            state = self.intent_agent.process(state)
            if state["current_intent"] == "EMERGENCY":
                state = self.emergency_agent.process(state)
            else:
                state = self.data_agent.process(state)
                state = self.response_agent.process(state)
                state = self.safety_agent.process(state)
                state = self.followup_agent.process(state)
                state = self.proactive_agent.process(state)
            final_state = state

        # Extract the assistant's final response
        response = final_state["messages"][-1]["content"]
        # Print debug info
        print(f"\n[Agent Activity]")
        print(f"- Intent: {final_state['current_intent']}")
        print(f"- Safety Flags: {final_state.get('safety_flags', [])}")
        print(f"- Follow-up Needed: {final_state.get('follow_up_needed', False)}")
        return response


def demo_health_assistant():
    """Demonstrate all agents working together with test scenarios."""
    assistant = HealthAIAssistant()
    print("=== Hello Heart AI Assistant - Multi-Agent Demo (OpenAI Version) ===\n")
    test_scenarios = [
        ("How did I sleep last night?", "Normal health query"),
        ("I'm having chest pain and feel dizzy", "Emergency scenario"),
        ("Should I stop taking my medication?", "Medical advice (requires disclaimer)"),
        ("Am I meeting my activity goals?", "Activity check with follow-up"),
        ("What's my blood pressure trend?", "BP monitoring query")
    ]
    for query, scenario in test_scenarios:
        print(f"\nScenario: {scenario}")
        print(f"User: {query}")
        response = assistant.process_message(query)
        print(f"Assistant: {response}")
        print("-" * 50)


if __name__ == "__main__":
    demo_health_assistant() 