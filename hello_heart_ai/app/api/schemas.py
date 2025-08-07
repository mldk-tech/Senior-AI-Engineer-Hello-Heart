"""
API schemas for Hello Heart AI Assistant.

This module defines all request and response models for the API endpoints.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field, validator


class MessageRole(str, Enum):
    """Message roles in conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class IntentType(str, Enum):
    """Intent classification types."""
    EMERGENCY = "EMERGENCY"
    HEALTH_QUERY = "HEALTH_QUERY"
    KNOWLEDGE_QUERY = "KNOWLEDGE_QUERY"
    MEDICAL_ADVICE = "MEDICAL_ADVICE"
    ACTIVITY_CHECK = "ACTIVITY_CHECK"
    SLEEP_INQUIRY = "SLEEP_INQUIRY"
    BP_MONITORING = "BP_MONITORING"
    OFF_TOPIC = "OFF_TOPIC"


class SafetyLevel(str, Enum):
    """Safety classification levels."""
    SAFE = "SAFE"
    CAUTION = "CAUTION"
    WARNING = "WARNING"
    EMERGENCY = "EMERGENCY"


class NudgeType(str, Enum):
    """Types of proactive nudges."""
    ACTIVITY_REMINDER = "ACTIVITY_REMINDER"
    SLEEP_REMINDER = "SLEEP_REMINDER"
    BP_CHECK = "BP_CHECK"
    BREATHING_EXERCISE = "BREATHING_EXERCISE"
    HYDRATION_REMINDER = "HYDRATION_REMINDER"
    MEDITATION_REMINDER = "MEDITATION_REMINDER"


# Base Models
class BaseRequest(BaseModel):
    """Base request model."""
    user_id: str = Field(..., description="Unique user identifier")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now, description="Request timestamp")


class BaseResponse(BaseModel):
    """Base response model."""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


# Chat Models
class ChatMessage(BaseModel):
    """Individual chat message."""
    role: MessageRole = Field(..., description="Message role")
    content: str = Field(..., description="Message content", min_length=1, max_length=5000)
    timestamp: Optional[datetime] = Field(default_factory=datetime.now, description="Message timestamp")


class ChatRequest(BaseRequest):
    """Chat request model."""
    message: str = Field(..., description="User message", min_length=1, max_length=5000)
    conversation_id: Optional[str] = Field(None, description="Conversation identifier for context")
    include_health_data: bool = Field(default=True, description="Whether to include health data in response")
    include_safety_check: bool = Field(default=True, description="Whether to perform safety checks")
    
    @validator('message')
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()


class ChatResponse(BaseResponse):
    """Chat response model."""
    response: str = Field(..., description="Assistant response")
    conversation_id: str = Field(..., description="Conversation identifier")
    intent: IntentType = Field(..., description="Classified intent")
    safety_level: SafetyLevel = Field(..., description="Safety classification")
    requires_medical_disclaimer: bool = Field(default=False, description="Whether medical disclaimer is required")
    follow_up_suggestions: List[str] = Field(default_factory=list, description="Follow-up suggestions")
    proactive_nudge: Optional[Dict[str, Any]] = Field(None, description="Proactive engagement nudge")
    health_insights: Optional[Dict[str, Any]] = Field(None, description="Health insights from data")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in response")


# Health Data Models
class HealthDataRequest(BaseRequest):
    """Health data request model."""
    data_types: List[str] = Field(default_factory=list, description="Types of health data to retrieve")
    date_range: Optional[Dict[str, datetime]] = Field(None, description="Date range for data retrieval")
    include_trends: bool = Field(default=True, description="Whether to include trend analysis")


class HealthDataResponse(BaseResponse):
    """Health data response model."""
    blood_pressure: Optional[Dict[str, Any]] = Field(None, description="Blood pressure data")
    heart_rate: Optional[Dict[str, Any]] = Field(None, description="Heart rate data")
    activity: Optional[Dict[str, Any]] = Field(None, description="Activity data")
    sleep: Optional[Dict[str, Any]] = Field(None, description="Sleep data")
    trends: Optional[Dict[str, Any]] = Field(None, description="Trend analysis")
    insights: List[str] = Field(default_factory=list, description="Health insights")


# User Models
class UserProfile(BaseModel):
    """User profile model."""
    user_id: str = Field(..., description="Unique user identifier")
    email: Optional[str] = Field(None, description="User email")
    name: Optional[str] = Field(None, description="User name")
    age: Optional[int] = Field(None, ge=0, le=150, description="User age")
    gender: Optional[str] = Field(None, description="User gender")
    health_goals: List[str] = Field(default_factory=list, description="User health goals")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")
    created_at: datetime = Field(default_factory=datetime.now, description="Profile creation time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Profile last update time")


class UserRegistration(BaseModel):
    """User registration model."""
    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password", min_length=8)
    name: Optional[str] = Field(None, description="User name")
    age: Optional[int] = Field(None, ge=0, le=150, description="User age")
    gender: Optional[str] = Field(None, description="User gender")
    health_goals: List[str] = Field(default_factory=list, description="User health goals")


class UserLogin(BaseModel):
    """User login model."""
    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")


class UserAuthResponse(BaseResponse):
    """User authentication response model."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user_profile: UserProfile = Field(..., description="User profile")


# Analytics Models
class AnalyticsRequest(BaseRequest):
    """Analytics request model."""
    metrics: List[str] = Field(..., description="Metrics to analyze")
    time_period: str = Field(..., description="Time period for analysis")
    include_comparisons: bool = Field(default=True, description="Whether to include comparisons")


class AnalyticsResponse(BaseResponse):
    """Analytics response model."""
    metrics: Dict[str, Any] = Field(..., description="Analytics metrics")
    trends: Dict[str, Any] = Field(..., description="Trend analysis")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    visualizations: Optional[Dict[str, Any]] = Field(None, description="Data visualizations")


# System Models
class SystemStatus(BaseModel):
    """System status model."""
    status: str = Field(..., description="System status")
    version: str = Field(..., description="Application version")
    uptime: float = Field(..., description="System uptime in seconds")
    memory_usage: Dict[str, float] = Field(..., description="Memory usage statistics")
    active_connections: int = Field(..., description="Active connections")
    last_health_check: datetime = Field(..., description="Last health check time")


class ConversationHistory(BaseModel):
    """Conversation history model."""
    conversation_id: str = Field(..., description="Conversation identifier")
    user_id: str = Field(..., description="User identifier")
    messages: List[ChatMessage] = Field(..., description="Conversation messages")
    created_at: datetime = Field(..., description="Conversation creation time")
    updated_at: datetime = Field(..., description="Conversation last update time")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Conversation metadata")


# Error Models
class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")


# Webhook Models
class WebhookPayload(BaseModel):
    """Webhook payload model."""
    event_type: str = Field(..., description="Event type")
    user_id: str = Field(..., description="User identifier")
    data: Dict[str, Any] = Field(..., description="Event data")
    timestamp: datetime = Field(default_factory=datetime.now, description="Event timestamp")


# Rate Limiting Models
class RateLimitInfo(BaseModel):
    """Rate limiting information."""
    limit: int = Field(..., description="Rate limit")
    remaining: int = Field(..., description="Remaining requests")
    reset_time: datetime = Field(..., description="Reset time")
    retry_after: Optional[int] = Field(None, description="Retry after seconds")


# Health Check Models
class HealthCheckResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Check timestamp")
    components: Dict[str, str] = Field(..., description="Component health status")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Environment")


# Notification Models
class NotificationRequest(BaseModel):
    """Notification request model."""
    user_id: str = Field(..., description="User identifier")
    notification_type: str = Field(..., description="Notification type")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    priority: str = Field(default="normal", description="Notification priority")
    scheduled_time: Optional[datetime] = Field(None, description="Scheduled time")


class NotificationResponse(BaseResponse):
    """Notification response model."""
    notification_id: str = Field(..., description="Notification identifier")
    scheduled_time: Optional[datetime] = Field(None, description="Scheduled time")
    delivery_status: str = Field(..., description="Delivery status") 