"""
Safety Check Agent for Hello Heart AI Assistant.

This agent validates responses for medical safety and ensures
appropriate disclaimers are present when needed.
"""

import re
from typing import List, Dict, Any
from datetime import datetime

from app.agents.base import BaseHealthAgent
from app.models.schemas import HealthAssistantState, Message
from app.core.config import get_settings


class SafetyCheckAgent(BaseHealthAgent):
    """Validates responses for medical safety using prompt engineering."""

    def __init__(self, llm=None):
        super().__init__(llm)
        self.settings = get_settings()
        self._initialize_safety_patterns()

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
        """Process the state and validate safety."""
        try:
            self.log_processing_start(state)
            
            if not self.validate_state(state):
                self.logger.error("Invalid state provided to SafetyCheckAgent")
                return state

            if not state.messages:
                self.logger.warning("No messages to validate")
                return state

            last_message = state.messages[-1]
            safety_flags = self._check_safety(last_message.content)
            
            # Add disclaimer if needed
            if self._should_add_disclaimer(state, last_message.content):
                safety_flags.append("NEEDS_DISCLAIMER")
                self._add_disclaimer(state)

            # Update state with safety flags
            state.safety_flags = safety_flags
            
            # Log safety check results
            if safety_flags:
                self.logger.warning(f"Safety flags raised: {safety_flags}")
            else:
                self.logger.info("Safety check passed - no issues detected")
                
            self.log_processing_end(state)
            return state
            
        except Exception as e:
            return self.handle_error(e, state)

    def _initialize_safety_patterns(self):
        """Initialize regex patterns for safety checking."""
        self.unsafe_patterns = [
            r"you have \w+ condition",
            r"stop taking",
            r"change your medication",
            r"this indicates \w+ disease",
            r"you should \w+ your medication",
            r"increase your dose",
            r"decrease your dose",
            r"you need to see a \w+ specialist",
            r"this is a sign of \w+",
            r"you are suffering from \w+"
        ]
        
        self.medical_advice_patterns = [
            r"take \w+ medication",
            r"prescribe \w+",
            r"diagnose \w+",
            r"treatment for \w+",
            r"medical condition",
            r"health condition"
        ]
        
        self.emergency_patterns = [
            r"call 911",
            r"emergency",
            r"immediately",
            r"urgent",
            r"critical"
        ]

    def _check_safety(self, content: str) -> List[str]:
        """Check content for safety issues."""
        safety_flags = []
        content_lower = content.lower()
        
        # Check for unsafe patterns
        for pattern in self.unsafe_patterns:
            if re.search(pattern, content_lower):
                safety_flags.append("UNSAFE_CONTENT")
                self.logger.warning(f"Unsafe content detected: {pattern}")
        
        # Check for medical advice patterns
        for pattern in self.medical_advice_patterns:
            if re.search(pattern, content_lower):
                safety_flags.append("MEDICAL_ADVICE_DETECTED")
                self.logger.info(f"Medical advice pattern detected: {pattern}")
        
        # Check for emergency content
        if any(re.search(pattern, content_lower) for pattern in self.emergency_patterns):
            safety_flags.append("EMERGENCY_VERIFIED")
            self.logger.info("Emergency response verified")
        
        return safety_flags

    def _should_add_disclaimer(self, state: HealthAssistantState, content: str) -> bool:
        """Determine if a medical disclaimer should be added."""
        # Check if disclaimer is required by state
        if state.requires_medical_disclaimer:
            return True
        
        # Check if content contains medical terms
        medical_terms = [
            "medication", "medicine", "pill", "dosage", "prescription",
            "diagnose", "diagnosis", "treatment", "doctor", "specialist",
            "symptom", "condition", "disease", "health"
        ]
        
        content_lower = content.lower()
        return any(term in content_lower for term in medical_terms)

    def _add_disclaimer(self, state: HealthAssistantState):
        """Add medical disclaimer to the last message."""
        if not state.messages:
            return
            
        disclaimer = ("\n\n*This is not medical advice. "
                     "Please consult your healthcare provider for personalized guidance.*")
        
        # Update the last message content
        last_message = state.messages[-1]
        last_message.content += disclaimer
        
        self.logger.info("Medical disclaimer added to response")

    def validate_emergency_response(self, content: str) -> bool:
        """Validate that emergency responses are appropriate."""
        content_lower = content.lower()
        
        # Check for required emergency elements
        has_emergency_call = "call 911" in content_lower or "emergency" in content_lower
        has_immediate_action = "immediately" in content_lower or "now" in content_lower
        has_safety_instruction = "stay calm" in content_lower or "sit down" in content_lower
        
        return has_emergency_call and has_immediate_action

    def get_safety_report(self, state: HealthAssistantState) -> Dict[str, Any]:
        """Generate a comprehensive safety report."""
        if not state.messages:
            return {"error": "No messages to analyze"}
        
        last_message = state.messages[-1]
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "message_id": len(state.messages),
            "safety_flags": state.safety_flags,
            "has_disclaimer": "not medical advice" in last_message.content.lower(),
            "word_count": len(last_message.content.split()),
            "emergency_response": self.validate_emergency_response(last_message.content),
            "risk_level": self._calculate_risk_level(state.safety_flags)
        }
        
        return report

    def _calculate_risk_level(self, safety_flags: List[str]) -> str:
        """Calculate overall risk level based on safety flags."""
        if "UNSAFE_CONTENT" in safety_flags:
            return "HIGH"
        elif "NEEDS_DISCLAIMER" in safety_flags:
            return "MEDIUM"
        elif "EMERGENCY_VERIFIED" in safety_flags:
            return "URGENT"
        else:
            return "LOW"

    def should_block_response(self, safety_flags: List[str]) -> bool:
        """Determine if response should be blocked."""
        return "UNSAFE_CONTENT" in safety_flags

    def get_safety_metrics(self, content: str) -> Dict[str, Any]:
        """Get detailed safety metrics for content."""
        return {
            "word_count": len(content.split()),
            "has_medical_terms": any(term in content.lower() for term in [
                "medication", "diagnosis", "treatment", "doctor"
            ]),
            "has_emergency_terms": any(term in content.lower() for term in [
                "emergency", "911", "urgent", "critical"
            ]),
            "has_disclaimer": "not medical advice" in content.lower(),
            "safety_score": self._calculate_safety_score(content)
        }

    def _calculate_safety_score(self, content: str) -> float:
        """Calculate a safety score (0-1, higher is safer)."""
        score = 1.0
        content_lower = content.lower()
        
        # Deduct points for risky content
        if any(pattern in content_lower for pattern in [
            "you have", "diagnose", "prescribe", "medication change"
        ]):
            score -= 0.5
        
        # Add points for safety measures
        if "not medical advice" in content_lower:
            score += 0.2
        if "consult your healthcare provider" in content_lower:
            score += 0.2
            
        return max(0.0, min(1.0, score)) 