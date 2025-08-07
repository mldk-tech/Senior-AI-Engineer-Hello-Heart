"""
Data models and schemas for Hello Heart AI Assistant.

This module defines all data structures using Pydantic models
for type safety and validation.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ConversationPhase(str, Enum):
    """Enumeration of conversation phases."""
    GREETING = "greeting"
    ASSESSMENT = "assessment"
    ADVICE = "advice"
    FOLLOW_UP = "follow_up"
    EMERGENCY = "emergency"


class BloodPressureReading(BaseModel):
    """Blood pressure reading data."""
    systolic: int = Field(..., ge=0, le=300)
    diastolic: int = Field(..., ge=0, le=200)
    timestamp: str = Field(..., description="ISO format timestamp")


class BloodPressureData(BaseModel):
    """Complete blood pressure data structure."""
    latest: BloodPressureReading
    trend: str = Field(..., description="Trend description")
    weekly_avg: BloodPressureReading


class HeartRateData(BaseModel):
    """Heart rate and HRV data."""
    resting_avg: int = Field(..., ge=0, le=200)
    active_avg: int = Field(..., ge=0, le=200)
    hrv: Dict[str, int] = Field(..., description="Heart rate variability data")


class StepsData(BaseModel):
    """Activity and steps data."""
    today: int = Field(..., ge=0)
    weekly_total: int = Field(..., ge=0)
    weekly_goal: int = Field(..., ge=0)
    daily_avg: int = Field(..., ge=0)


class SleepData(BaseModel):
    """Sleep quality and duration data."""
    last_night: Dict[str, Any] = Field(..., description="Last night's sleep data")
    weekly_avg_hours: float = Field(..., ge=0, le=24)


class UserHealthData(BaseModel):
    """Complete user health data structure."""
    user_id: str = Field(..., description="Unique user identifier")
    blood_pressure: BloodPressureData
    heart_rate: HeartRateData
    steps: StepsData
    sleep: SleepData


class Message(BaseModel):
    """Chat message structure."""
    role: str = Field(..., description="Message role (user/assistant)")
    content: str = Field(..., description="Message content")
    timestamp: str = Field(..., description="ISO format timestamp")
    priority: Optional[str] = Field(None, description="Message priority level")


class HealthAssistantState(BaseModel):
    """State management for the health assistant workflow."""
    messages: List[Message] = Field(default_factory=list)
    user_health_data: Dict[str, Any] = Field(default_factory=dict)
    current_intent: str = Field(default="")
    requires_medical_disclaimer: bool = Field(default=False)
    conversation_phase: str = Field(default=ConversationPhase.ASSESSMENT.value)
    follow_up_needed: bool = Field(default=False)
    safety_flags: List[str] = Field(default_factory=list)
    proactive_nudge: Optional[str] = Field(default=None)
    
    class Config:
        # Allow extra fields for flexibility
        extra = "allow"


class AgentResponse(BaseModel):
    """Standard response structure for agents."""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data")
    safety_flags: List[str] = Field(default_factory=list)


class EmergencyAlert(BaseModel):
    """Emergency alert structure."""
    user_id: str = Field(..., description="User identifier")
    timestamp: datetime = Field(default_factory=datetime.now)
    symptoms: List[str] = Field(..., description="Reported symptoms")
    severity: str = Field(..., description="Emergency severity level")
    action_taken: str = Field(..., description="Action taken by the system")


class ProactiveNudge(BaseModel):
    """Proactive engagement nudge structure."""
    nudge_type: str = Field(..., description="Type of nudge")
    message: str = Field(..., description="Nudge message")
    scheduled_time: Optional[datetime] = Field(None, description="Scheduled time")
    user_id: str = Field(..., description="Target user")
    priority: str = Field(default="normal", description="Nudge priority")


# Type aliases for backward compatibility
HealthData = UserHealthData
State = HealthAssistantState 