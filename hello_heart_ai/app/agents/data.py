"""
Data Retrieval Agent for Hello Heart AI Assistant.

This agent retrieves and contextualizes health data based on user queries.
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime

from app.agents.base import BaseHealthAgent
from app.models.schemas import HealthAssistantState, UserHealthData
from app.core.config import get_settings


class DataRetrievalAgent(BaseHealthAgent):
    """Retrieves and contextualizes health data using prompt engineering."""

    def __init__(self, user_data: Optional[Dict[str, Any]] = None, llm: Optional[Any] = None):
        super().__init__(llm)
        self.settings = get_settings()
        self.user_data = user_data or self._load_mock_data()

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
        """Process the state and retrieve relevant health data."""
        try:
            self.log_processing_start(state)
            
            if not self.validate_state(state):
                self.logger.error("Invalid state provided to DataRetrievalAgent")
                return state

            intent = state.current_intent
            relevant_data = self._get_relevant_data(intent)
            
            # Update state with retrieved data
            state.user_health_data = relevant_data
            
            self.logger.info(f"Retrieved data for intent: {intent}")
            self.log_processing_end(state)
            
            return state
            
        except Exception as e:
            return self.handle_error(e, state)

    def _load_mock_data(self) -> Dict[str, Any]:
        """Load mock health data from JSON file."""
        try:
            # Try multiple possible paths for the mock data file
            possible_paths = [
                # Path relative to the data agent file
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "mock_user_data.json"),
                # Path relative to project root
                os.path.join(os.getcwd(), "hello_heart_ai", "data", "mock_user_data.json"),
                # Path relative to current working directory
                os.path.join(os.getcwd(), "data", "mock_user_data.json"),
                # Direct path from settings
                self.settings.mock_data_path
            ]
            
            data_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    data_path = path
                    break
            
            if data_path is None:
                raise FileNotFoundError(f"Mock data file not found in any of the expected locations: {possible_paths}")
            
            with open(data_path, 'r') as f:
                data = json.load(f)
                
            self.logger.info(f"Loaded mock health data from: {data_path}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error loading mock data: {e}")
            # Fallback to hardcoded data
            return {
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

    def _get_relevant_data(self, intent: str) -> Dict[str, Any]:
        """Get relevant health data based on user intent."""
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
            # General health overview
            relevant_data = {
                "blood_pressure": self.user_data["blood_pressure"]["latest"],
                "steps_today": self.user_data["steps"]["today"],
                "sleep_quality": self.user_data["sleep"]["last_night"]["quality_score"],
                "hrv": self.user_data["heart_rate"]["hrv"]["current"]
            }

        return relevant_data

    def get_data_summary(self, intent: str) -> Dict[str, Any]:
        """Get a summary of available data for the given intent."""
        data = self._get_relevant_data(intent)
        
        summary = {
            "intent": intent,
            "data_available": bool(data),
            "data_points": len(data),
            "timestamp": datetime.now().isoformat()
        }
        
        if data:
            summary["data_types"] = list(data.keys())
            
        return summary

    def validate_health_data(self, data: Dict[str, Any]) -> bool:
        """Validate health data for completeness and reasonableness."""
        try:
            # Check for required fields
            required_fields = ["user_id", "blood_pressure", "heart_rate", "steps", "sleep"]
            
            for field in required_fields:
                if field not in data:
                    self.logger.warning(f"Missing required field: {field}")
                    return False
            
            # Validate blood pressure values
            bp = data["blood_pressure"]["latest"]
            if not (0 <= bp["systolic"] <= 300 and 0 <= bp["diastolic"] <= 200):
                self.logger.warning("Blood pressure values out of reasonable range")
                return False
            
            # Validate heart rate values
            hr = data["heart_rate"]
            if not (0 <= hr["resting_avg"] <= 200 and 0 <= hr["active_avg"] <= 200):
                self.logger.warning("Heart rate values out of reasonable range")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating health data: {e}")
            return False

    def get_trend_analysis(self, data_type: str) -> Dict[str, Any]:
        """Analyze trends for a specific data type."""
        if data_type not in self.user_data:
            return {"error": f"Data type {data_type} not available"}
        
        data = self.user_data[data_type]
        analysis = {
            "data_type": data_type,
            "has_trend": "trend" in data,
            "current_status": "unknown"
        }
        
        if data_type == "blood_pressure" and "trend" in data:
            analysis["current_status"] = data["trend"]
        elif data_type == "steps":
            progress = (data["weekly_total"] / data["weekly_goal"]) * 100
            if progress >= 100:
                analysis["current_status"] = "goal_achieved"
            elif progress >= 75:
                analysis["current_status"] = "on_track"
            else:
                analysis["current_status"] = "needs_improvement"
                
        return analysis 