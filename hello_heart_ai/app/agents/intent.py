"""
Intent Classification Agent for Hello Heart AI Assistant.

This agent analyzes user messages to determine their intent
and routes them to appropriate specialized agents.
"""

import re
from typing import Dict, Any
from datetime import datetime

from app.agents.base import BaseHealthAgent
from app.models.schemas import HealthAssistantState, ConversationPhase


class IntentClassificationAgent(BaseHealthAgent):
    """Classifies user intent using advanced prompt engineering and heuristics."""

    def get_system_prompt(self) -> str:
        return """You are an Intent Classification Agent for a health assistant.
        
Your task is to classify user messages into one of these categories:
1. EMERGENCY - Medical emergencies requiring immediate attention
2. HEALTH_QUERY - General health questions about their data
3. KNOWLEDGE_QUERY - Questions about health knowledge, medical information, or educational content
4. MEDICAL_ADVICE - Requests for diagnosis or medication changes
5. ACTIVITY_CHECK - Questions about steps, exercise, or movement
6. SLEEP_INQUIRY - Questions about sleep patterns
7. BP_MONITORING - Blood pressure related queries
8. OFF_TOPIC - Non-health related queries

Emergency indicators include: chest pain, breathing difficulty, severe symptoms, extreme vital signs.
Medical advice includes: medication questions, diagnosis requests, treatment plans.

Respond with ONLY the category name, nothing else."""

    def process(self, state: HealthAssistantState) -> HealthAssistantState:
        """Process the state and classify user intent."""
        try:
            self.log_processing_start(state)
            
            if not self.validate_state(state):
                self.logger.error("Invalid state provided to IntentClassificationAgent")
                return state

            last_message = state.messages[-1].content if state.messages else ""
            
            # Classify intent using heuristics
            intent = self._classify_intent(last_message)
            
            # Update state with classification results
            state.current_intent = intent
            state.conversation_phase = self._get_conversation_phase(intent)
            state.requires_medical_disclaimer = self._requires_disclaimer(intent)
            
            self.logger.info(f"Classified intent: {intent}")
            self.log_processing_end(state)
            
            return state
            
        except Exception as e:
            return self.handle_error(e, state)

    def _classify_intent(self, message: str) -> str:
        """Classify user intent using keyword matching and heuristics."""
        message_lower = message.lower()
        
        # Emergency keywords - highest priority
        emergency_keywords = [
            "chest pain", "can't breathe", "emergency", "severe", 
            "dizzy", "fainted", "heart attack", "stroke", "unconscious"
        ]
        
        if any(keyword in message_lower for keyword in emergency_keywords):
            return "EMERGENCY"
        
        # Medical advice keywords
        medical_keywords = [
            "diagnose", "medication", "prescription", "doctor", 
            "treatment", "medicine", "pill", "dosage"
        ]
        
        if any(keyword in message_lower for keyword in medical_keywords):
            return "MEDICAL_ADVICE"
        
        # Activity-related keywords
        activity_keywords = [
            "step", "walk", "active", "exercise", "workout", 
            "activity", "movement", "fitness"
        ]
        
        if any(keyword in message_lower for keyword in activity_keywords):
            return "ACTIVITY_CHECK"
        
        # Sleep-related keywords
        sleep_keywords = [
            "sleep", "rest", "bed", "tired", "insomnia", 
            "dream", "night", "morning"
        ]
        
        if any(keyword in message_lower for keyword in sleep_keywords):
            return "SLEEP_INQUIRY"
        
        # Blood pressure keywords
        bp_keywords = [
            "pressure", "bp", "blood pressure", "systolic", 
            "diastolic", "hypertension"
        ]
        
        if any(keyword in message_lower for keyword in bp_keywords):
            return "BP_MONITORING"
        
        # Knowledge query keywords
        knowledge_keywords = [
            "what is", "how does", "why", "explain", "tell me about",
            "information", "knowledge", "learn", "understand", "benefits",
            "risks", "effects", "impact", "cause", "prevent", "improve"
        ]
        
        if any(keyword in message_lower for keyword in knowledge_keywords):
            return "KNOWLEDGE_QUERY"
        
        # Default to general health query
        return "HEALTH_QUERY"

    def _get_conversation_phase(self, intent: str) -> str:
        """Determine conversation phase based on intent."""
        if intent == "EMERGENCY":
            return ConversationPhase.EMERGENCY.value
        elif intent == "MEDICAL_ADVICE":
            return ConversationPhase.ADVICE.value
        else:
            return ConversationPhase.ASSESSMENT.value

    def _requires_disclaimer(self, intent: str) -> bool:
        """Determine if medical disclaimer is required."""
        return intent in ["EMERGENCY", "MEDICAL_ADVICE"]

    def get_intent_confidence(self, message: str) -> Dict[str, float]:
        """Get confidence scores for different intents."""
        message_lower = message.lower()
        scores = {
            "EMERGENCY": 0.0,
            "MEDICAL_ADVICE": 0.0,
            "KNOWLEDGE_QUERY": 0.0,
            "ACTIVITY_CHECK": 0.0,
            "SLEEP_INQUIRY": 0.0,
            "BP_MONITORING": 0.0,
            "HEALTH_QUERY": 0.0
        }
        
        # Calculate confidence based on keyword matches
        emergency_keywords = ["chest pain", "can't breathe", "emergency", "severe"]
        medical_keywords = ["diagnose", "medication", "prescription", "doctor"]
        knowledge_keywords = ["what is", "how does", "why", "explain", "tell me about"]
        activity_keywords = ["step", "walk", "active", "exercise"]
        sleep_keywords = ["sleep", "rest", "bed", "tired"]
        bp_keywords = ["pressure", "bp", "blood pressure"]
        
        # Count matches for each category
        for keyword in emergency_keywords:
            if keyword in message_lower:
                scores["EMERGENCY"] += 0.25
        
        for keyword in medical_keywords:
            if keyword in message_lower:
                scores["MEDICAL_ADVICE"] += 0.25
                
        for keyword in knowledge_keywords:
            if keyword in message_lower:
                scores["KNOWLEDGE_QUERY"] += 0.25
                
        for keyword in activity_keywords:
            if keyword in message_lower:
                scores["ACTIVITY_CHECK"] += 0.25
                
        for keyword in sleep_keywords:
            if keyword in message_lower:
                scores["SLEEP_INQUIRY"] += 0.25
                
        for keyword in bp_keywords:
            if keyword in message_lower:
                scores["BP_MONITORING"] += 0.25
        
        # Default confidence for general health query
        if all(score == 0.0 for score in scores.values()):
            scores["HEALTH_QUERY"] = 0.5
            
        return scores 