"""
Follow-up and Proactive Engagement Agents for Hello Heart AI Assistant.

This module contains agents for determining follow-up needs and
managing proactive engagement with users.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from app.agents.base import BaseHealthAgent
from app.models.schemas import HealthAssistantState, ProactiveNudge
from app.core.config import get_settings


class FollowUpAgent(BaseHealthAgent):
    """Determines need for proactive follow-ups using prompt engineering."""

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
        """Process the state and determine follow-up needs."""
        try:
            self.log_processing_start(state)
            
            if not self.validate_state(state):
                self.logger.error("Invalid state provided to FollowUpAgent")
                return state

            health_data = state.user_health_data
            follow_up_needed = False
            proactive_nudge = None

            # Check activity goals
            if "steps" in health_data:
                progress_str = health_data.get("weekly_progress", "0%")
                try:
                    progress = float(progress_str.rstrip("%"))
                    if progress < 50:
                        follow_up_needed = True
                        proactive_nudge = (
                            f"You're at {progress_str} of your weekly step goal. "
                            "A 10-minute walk could boost your energy! "
                            "Shall I remind you later?"
                        )
                        self.logger.info(f"Low activity detected: {progress_str}")
                except ValueError:
                    self.logger.warning(f"Could not parse progress: {progress_str}")

            # Check sleep quality
            if "sleep" in health_data:
                quality = health_data["sleep"]["last_night"]["quality_score"]
                if quality < 60:
                    follow_up_needed = True
                    proactive_nudge = (
                        "Your sleep quality was lower last night. "
                        "Would you like some tips for better rest tonight?"
                    )
                    self.logger.info(f"Poor sleep quality detected: {quality}%")

            # Check blood pressure trends
            if "blood_pressure" in health_data:
                bp_data = health_data["blood_pressure"]
                if "trend" in bp_data and "worsening" in bp_data["trend"].lower():
                    follow_up_needed = True
                    proactive_nudge = (
                        "I notice your blood pressure trend is concerning. "
                        "Would you like to discuss this with your healthcare provider?"
                    )
                    self.logger.info("Concerning BP trend detected")

            # Update state
            state.follow_up_needed = follow_up_needed
            state.proactive_nudge = proactive_nudge

            if follow_up_needed:
                self.logger.info(f"Follow-up needed: {proactive_nudge}")
            else:
                self.logger.info("No follow-up needed")

            self.log_processing_end(state)
            return state
            
        except Exception as e:
            return self.handle_error(e, state)

    def get_follow_up_metrics(self, health_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get metrics for follow-up analysis."""
        metrics = {
            "activity_score": 0.0,
            "sleep_score": 0.0,
            "bp_score": 0.0,
            "overall_score": 0.0
        }

        # Activity score
        if "steps" in health_data:
            progress_str = health_data.get("weekly_progress", "0%")
            try:
                progress = float(progress_str.rstrip("%"))
                metrics["activity_score"] = progress / 100.0
            except ValueError:
                metrics["activity_score"] = 0.0

        # Sleep score
        if "sleep" in health_data:
            quality = health_data["sleep"]["last_night"]["quality_score"]
            metrics["sleep_score"] = quality / 100.0

        # BP score (simplified)
        if "blood_pressure" in health_data:
            bp_data = health_data["blood_pressure"]
            if "trend" in bp_data:
                if "improving" in bp_data["trend"].lower():
                    metrics["bp_score"] = 1.0
                elif "stable" in bp_data["trend"].lower():
                    metrics["bp_score"] = 0.7
                else:
                    metrics["bp_score"] = 0.3

        # Overall score
        scores = [metrics["activity_score"], metrics["sleep_score"], metrics["bp_score"]]
        metrics["overall_score"] = sum(scores) / len(scores) if scores else 0.0

        return metrics


class ProactiveEngagementAgent(BaseHealthAgent):
    """Manages proactive nudges and engagement using prompt engineering."""

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
        """Process the state and manage proactive engagement."""
        try:
            self.log_processing_start(state)
            
            if not self.validate_state(state):
                self.logger.error("Invalid state provided to ProactiveEngagementAgent")
                return state

            if state.follow_up_needed and state.proactive_nudge:
                # In production, this would schedule a notification
                # For now, we just log it
                self.logger.info(f"Proactive nudge scheduled: {state.proactive_nudge}")
                
                # Create nudge object for tracking
                nudge = ProactiveNudge(
                    nudge_type="GENTLE_REMINDER",
                    message=state.proactive_nudge,
                    scheduled_time=datetime.now() + timedelta(hours=2),  # Schedule for 2 hours later
                    user_id="user123",  # In production, get from state
                    priority="normal"
                )
                
                # Log nudge creation
                self.logger.info(f"Created nudge: {nudge.nudge_type} - {nudge.message[:50]}...")
                
            else:
                self.logger.info("No proactive engagement needed")

            self.log_processing_end(state)
            return state
            
        except Exception as e:
            return self.handle_error(e, state)

    def should_send_nudge(self, user_id: str, nudge_type: str) -> bool:
        """Determine if a nudge should be sent based on timing and frequency."""
        # In production, this would check user preferences and timing
        # For now, return True if it's a reasonable time
        current_hour = datetime.now().hour
        return 8 <= current_hour <= 21  # Between 8 AM and 9 PM

    def get_engagement_metrics(self, state: HealthAssistantState) -> Dict[str, Any]:
        """Get metrics for engagement analysis."""
        return {
            "follow_up_needed": state.follow_up_needed,
            "has_proactive_nudge": bool(state.proactive_nudge),
            "nudge_type": "GENTLE_REMINDER" if state.proactive_nudge else None,
            "timestamp": datetime.now().isoformat(),
            "user_engagement_level": self._calculate_engagement_level(state)
        }

    def _calculate_engagement_level(self, state: HealthAssistantState) -> str:
        """Calculate user engagement level."""
        # Simple heuristic based on message count and follow-up needs
        message_count = len(state.messages) if state.messages else 0
        
        if message_count > 10:
            return "HIGH"
        elif message_count > 5:
            return "MEDIUM"
        else:
            return "LOW"

    def create_celebration_nudge(self, achievement: str) -> ProactiveNudge:
        """Create a celebration nudge for achievements."""
        return ProactiveNudge(
            nudge_type="CELEBRATION",
            message=f"🎉 Congratulations! You've achieved: {achievement}",
            scheduled_time=datetime.now(),
            user_id="user123",
            priority="high"
        )

    def create_reminder_nudge(self, reminder_type: str, message: str) -> ProactiveNudge:
        """Create a reminder nudge."""
        return ProactiveNudge(
            nudge_type="GENTLE_REMINDER",
            message=message,
            scheduled_time=datetime.now() + timedelta(hours=1),
            user_id="user123",
            priority="normal"
        ) 