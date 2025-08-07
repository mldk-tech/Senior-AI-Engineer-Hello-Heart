"""
Response Generation Agent for Hello Heart AI Assistant.

This agent generates personalized, compassionate responses based on
user intent and health data.
"""

from typing import Dict, Any
from datetime import datetime

from app.agents.base import BaseHealthAgent
from app.models.schemas import HealthAssistantState, Message


class ResponseGenerationAgent(BaseHealthAgent):
    """Generates personalized responses using advanced prompt engineering."""

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
        """Process the state and generate a personalized response."""
        try:
            self.log_processing_start(state)
            
            if not self.validate_state(state):
                self.logger.error("Invalid state provided to ResponseGenerationAgent")
                return state

            intent = state.current_intent
            health_data = state.user_health_data

            # Generate response based on intent
            response = self._generate_response(intent, health_data)
            
            # Create message object
            message = Message(
                role="assistant",
                content=response,
                timestamp=datetime.now().isoformat()
            )
            
            # Add message to state
            state.messages.append(message)
            
            self.logger.info(f"Generated response for intent: {intent}")
            self.log_processing_end(state)
            
            return state
            
        except Exception as e:
            return self.handle_error(e, state)

    def _generate_response(self, intent: str, health_data: Dict[str, Any]) -> str:
        """Generate response based on intent and health data."""
        if intent == "EMERGENCY":
            return self._generate_emergency_response()
        elif intent == "ACTIVITY_CHECK":
            return self._generate_activity_response(health_data)
        elif intent == "SLEEP_INQUIRY":
            return self._generate_sleep_response(health_data)
        elif intent == "BP_MONITORING":
            return self._generate_bp_response(health_data)
        elif intent == "MEDICAL_ADVICE":
            return self._generate_medical_advice_response()
        else:
            return self._generate_general_response(health_data)

    def _generate_activity_response(self, data: Dict[str, Any]) -> str:
        """Generate response for activity-related queries."""
        if "steps" in data:
            steps = data["steps"]
            progress = data.get("weekly_progress", "0%")
            return (f"You're doing great! You've taken {steps['today']:,} steps today "
                    f"and you're at {progress} of your weekly goal. "
                    f"That's {steps['daily_avg']:,} steps on average this week. "
                    f"Keep up the momentum! Would you like a reminder for an evening walk?")
        return "Let me help you track your activity. Could you sync your device first?"

    def _generate_sleep_response(self, data: Dict[str, Any]) -> str:
        """Generate response for sleep-related queries."""
        if "sleep" in data:
            sleep = data["sleep"]["last_night"]
            return (f"You slept {sleep['hours']} hours last night with a quality score of "
                    f"{sleep['quality_score']}%. That's close to the recommended 7-8 hours! "
                    f"To improve further, try a consistent bedtime routine. "
                    f"How do you feel this morning?")
        return "I'd love to help with your sleep. Please sync your device for the latest data."

    def _generate_bp_response(self, data: Dict[str, Any]) -> str:
        """Generate response for blood pressure queries."""
        if "blood_pressure" in data:
            bp = data["blood_pressure"]["latest"] if "latest" in data["blood_pressure"] else data["blood_pressure"]
            trend = data["blood_pressure"].get("trend", "")
            return (f"Your latest reading is {bp['systolic']}/{bp['diastolic']} mmHg - "
                    f"that's in a healthy range! Your trend shows {trend} progress. "
                    f"Keep up your healthy habits. When did you last take your medication?")
        return "Let's check your blood pressure. When was your last reading?"

    def _generate_emergency_response(self) -> str:
        """Generate emergency response."""
        return ("I'm concerned about your symptoms. Please call 911 or your emergency number "
                "immediately. If someone is with you, ask them to help. "
                "Your safety is the top priority.")

    def _generate_medical_advice_response(self) -> str:
        """Generate response for medical advice requests."""
        return ("I understand you have questions about your health. While I can help you "
                "understand your data, I cannot provide medical advice. Please consult "
                "your healthcare provider for personalized medical guidance.")

    def _generate_general_response(self, data: Dict[str, Any]) -> str:
        """Generate general health response."""
        return ("I'm here to help you understand your health better. "
                "What specific aspect would you like to explore - "
                "your activity, sleep, or blood pressure?")

    def get_response_metrics(self, response: str) -> Dict[str, Any]:
        """Analyze response for various metrics."""
        return {
            "word_count": len(response.split()),
            "has_encouragement": any(word in response.lower() for word in ["great", "good", "excellent", "fantastic"]),
            "has_action_item": any(word in response.lower() for word in ["try", "should", "could", "would"]),
            "has_question": "?" in response,
            "tone": self._analyze_tone(response)
        }

    def _analyze_tone(self, response: str) -> str:
        """Analyze the tone of the response."""
        response_lower = response.lower()
        
        if any(word in response_lower for word in ["concerned", "worried", "emergency"]):
            return "urgent"
        elif any(word in response_lower for word in ["great", "excellent", "fantastic", "amazing"]):
            return "encouraging"
        elif any(word in response_lower for word in ["try", "suggest", "recommend"]):
            return "helpful"
        else:
            return "neutral"

    def should_add_disclaimer(self, intent: str, response: str) -> bool:
        """Determine if a medical disclaimer should be added."""
        disclaimer_triggers = [
            "medication", "medicine", "pill", "dosage", "prescription",
            "diagnose", "diagnosis", "treatment", "doctor", "specialist"
        ]
        
        return (intent == "MEDICAL_ADVICE" or 
                any(trigger in response.lower() for trigger in disclaimer_triggers)) 