"""
Health data router for Hello Heart AI Assistant API.

This module provides endpoints for health data retrieval, analysis,
and insights generation.
"""

import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
import structlog

from app.api.schemas import (
    HealthDataRequest, HealthDataResponse, SystemStatus,
    HealthCheckResponse
)
from app.api.dependencies import (
    get_current_user, validate_health_data_access,
    get_cached_health_data, cache_health_data
)
from app.core.monitoring import get_metrics_collector, get_health_checker
from app.core.config import get_settings

# Structured logging
logger = structlog.get_logger()

# Create router
router = APIRouter()


@router.get("/data/{user_id}", response_model=HealthDataResponse)
async def get_health_data(
    user_id: str,
    data_type: str = "all",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """Get general health data for a user."""
    try:
        # Validate access
        if not await validate_health_data_access(user_id, data_type, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to health data"
            )
        
        # Check cache first
        cache_key = f"{user_id}:health_data:{data_type}"
        cached_data = await get_cached_health_data(user_id, f"health_data_{data_type}")
        
        if cached_data:
            logger.info(
                "Health data retrieved from cache",
                user_id=user_id,
                data_type=data_type
            )
            return HealthDataResponse(**cached_data)
        
        # Mock health data (in a real app, this would come from a database)
        health_data = {
            "user_id": user_id,
            "data_type": data_type,
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "steps": 6500,
                "calories": 1800,
                "active_minutes": 45,
                "heart_rate_avg": 72,
                "sleep_hours": 7.2,
                "blood_pressure": "128/82"
            },
            "goals": {
                "daily_steps": 10000,
                "weekly_workouts": 3,
                "sleep_target": 8
            },
            "trends": {
                "steps_trend": "increasing",
                "heart_rate_trend": "stable",
                "sleep_trend": "improving"
            }
        }
        
        # Cache the data
        await cache_health_data(user_id, f"health_data_{data_type}", health_data)
        
        # Record metrics
        metrics_collector = get_metrics_collector()
        metrics_collector.record_health_data_request(data_type, False)  # Cache miss
        
        logger.info(
            "Health data retrieved",
            user_id=user_id,
            data_type=data_type
        )
        
        return HealthDataResponse(**health_data)
        
    except Exception as e:
        logger.error(
            "Error retrieving health data",
            user_id=user_id,
            data_type=data_type,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve health data"
        )


@router.get("/blood-pressure/{user_id}")
async def get_blood_pressure_data(
    user_id: str,
    days: int = Query(7, description="Number of days to retrieve"),
    current_user = Depends(get_current_user)
):
    """Get blood pressure data for a user."""
    try:
        # Validate access
        if not await validate_health_data_access(user_id, "blood_pressure", current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to blood pressure data"
            )
        
        # Check cache
        cached_data = await get_cached_health_data(user_id, f"blood_pressure_{days}")
        
        if cached_data:
            logger.info(
                "Blood pressure data retrieved from cache",
                user_id=user_id,
                days=days
            )
            return cached_data
        
        # Mock blood pressure data
        bp_data = {
            "user_id": user_id,
            "data_type": "blood_pressure",
            "days": days,
            "timestamp": datetime.now().isoformat(),
            "readings": [
                {"date": "2024-01-15", "systolic": 128, "diastolic": 82, "time": "08:00"},
                {"date": "2024-01-14", "systolic": 132, "diastolic": 85, "time": "08:00"},
                {"date": "2024-01-13", "systolic": 130, "diastolic": 83, "time": "08:00"}
            ],
            "average": {"systolic": 130, "diastolic": 83},
            "trend": "stable"
        }
        
        # Cache the data
        await cache_health_data(user_id, f"blood_pressure_{days}", bp_data)
        
        # Record metrics
        metrics_collector = get_metrics_collector()
        metrics_collector.record_health_data_request("blood_pressure", False)
        
        logger.info(
            "Blood pressure data retrieved",
            user_id=user_id,
            days=days
        )
        
        return bp_data
        
    except Exception as e:
        logger.error(
            "Error retrieving blood pressure data",
            user_id=user_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve blood pressure data"
        )


@router.get("/activity/{user_id}")
async def get_activity_data(
    user_id: str,
    days: int = Query(7, description="Number of days to retrieve"),
    current_user = Depends(get_current_user)
):
    """Get activity data for a user."""
    try:
        # Validate access
        if not await validate_health_data_access(user_id, "activity", current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to activity data"
            )
        
        # Check cache
        cached_data = await get_cached_health_data(user_id, f"activity_{days}")
        
        if cached_data:
            logger.info(
                "Activity data retrieved from cache",
                user_id=user_id,
                days=days
            )
            return cached_data
        
        # Mock activity data
        activity_data = {
            "user_id": user_id,
            "data_type": "activity",
            "days": days,
            "timestamp": datetime.now().isoformat(),
            "daily_activity": [
                {"date": "2024-01-15", "steps": 6500, "calories": 1800, "active_minutes": 45},
                {"date": "2024-01-14", "steps": 7200, "calories": 1950, "active_minutes": 52},
                {"date": "2024-01-13", "steps": 5800, "calories": 1650, "active_minutes": 38}
            ],
            "weekly_summary": {
                "total_steps": 19500,
                "total_calories": 5400,
                "total_active_minutes": 135,
                "goal_completion": 78
            }
        }
        
        # Cache the data
        await cache_health_data(user_id, f"activity_{days}", activity_data)
        
        # Record metrics
        metrics_collector = get_metrics_collector()
        metrics_collector.record_health_data_request("activity", False)
        
        logger.info(
            "Activity data retrieved",
            user_id=user_id,
            days=days
        )
        
        return activity_data
        
    except Exception as e:
        logger.error(
            "Error retrieving activity data",
            user_id=user_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve activity data"
        )


@router.get("/sleep/{user_id}")
async def get_sleep_data(
    user_id: str,
    days: int = Query(7, description="Number of days to retrieve"),
    current_user = Depends(get_current_user)
):
    """Get sleep data for a user."""
    try:
        # Validate access
        if not await validate_health_data_access(user_id, "sleep", current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to sleep data"
            )
        
        # Check cache
        cached_data = await get_cached_health_data(user_id, f"sleep_{days}")
        
        if cached_data:
            logger.info(
                "Sleep data retrieved from cache",
                user_id=user_id,
                days=days
            )
            return cached_data
        
        # Mock sleep data
        sleep_data = {
            "user_id": user_id,
            "data_type": "sleep",
            "days": days,
            "timestamp": datetime.now().isoformat(),
            "sleep_records": [
                {"date": "2024-01-15", "duration": 7.2, "quality": 78, "deep_sleep": 2.1},
                {"date": "2024-01-14", "duration": 6.8, "quality": 72, "deep_sleep": 1.8},
                {"date": "2024-01-13", "duration": 7.5, "quality": 82, "deep_sleep": 2.3}
            ],
            "weekly_average": {
                "duration": 7.2,
                "quality": 77,
                "deep_sleep": 2.1
            }
        }
        
        # Cache the data
        await cache_health_data(user_id, f"sleep_{days}", sleep_data)
        
        # Record metrics
        metrics_collector = get_metrics_collector()
        metrics_collector.record_health_data_request("sleep", False)
        
        logger.info(
            "Sleep data retrieved",
            user_id=user_id,
            days=days
        )
        
        return sleep_data
        
    except Exception as e:
        logger.error(
            "Error retrieving sleep data",
            user_id=user_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sleep data"
        )


@router.get("/heart-rate/{user_id}")
async def get_heart_rate_data(
    user_id: str,
    days: int = Query(7, description="Number of days to retrieve"),
    current_user = Depends(get_current_user)
):
    """Get heart rate data for a user."""
    try:
        # Validate access
        if not await validate_health_data_access(user_id, "heart_rate", current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to heart rate data"
            )
        
        # Check cache
        cached_data = await get_cached_health_data(user_id, f"heart_rate_{days}")
        
        if cached_data:
            logger.info(
                "Heart rate data retrieved from cache",
                user_id=user_id,
                days=days
            )
            return cached_data
        
        # Mock heart rate data
        hr_data = {
            "user_id": user_id,
            "data_type": "heart_rate",
            "days": days,
            "timestamp": datetime.now().isoformat(),
            "daily_averages": [
                {"date": "2024-01-15", "resting": 68, "active": 120, "hrv": 45},
                {"date": "2024-01-14", "resting": 70, "active": 125, "hrv": 42},
                {"date": "2024-01-13", "resting": 66, "active": 118, "hrv": 48}
            ],
            "weekly_summary": {
                "avg_resting": 68,
                "avg_active": 121,
                "avg_hrv": 45,
                "trend": "improving"
            }
        }
        
        # Cache the data
        await cache_health_data(user_id, f"heart_rate_{days}", hr_data)
        
        # Record metrics
        metrics_collector = get_metrics_collector()
        metrics_collector.record_health_data_request("heart_rate", False)
        
        logger.info(
            "Heart rate data retrieved",
            user_id=user_id,
            days=days
        )
        
        return hr_data
        
    except Exception as e:
        logger.error(
            "Error retrieving heart rate data",
            user_id=user_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve heart rate data"
        )


@router.get("/insights/{user_id}")
async def get_health_insights(
    user_id: str,
    insight_type: Optional[str] = Query(None, description="Type of insights to generate"),
    current_user = Depends(get_current_user),
    assistant = Depends(get_assistant)
):
    """Get personalized health insights."""
    try:
        # Validate access
        await validate_health_data_access(user_id, "insights", current_user)
        
        # Generate insights based on health data
        insights = await _generate_personalized_insights(user_id, insight_type, assistant)
        
        return {
            "success": True,
            "message": "Insights generated successfully",
            "insights": insights,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error generating insights", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate insights"
        )


@router.get("/trends/{user_id}")
async def get_health_trends(
    user_id: str,
    metric: str = Query(..., description="Health metric to analyze"),
    period: str = Query("7d", description="Analysis period"),
    current_user = Depends(get_current_user)
):
    """Get trend analysis for health metrics."""
    try:
        # Validate access
        await validate_health_data_access(user_id, "trends", current_user)
        
        # Generate trend analysis
        trends = await _analyze_health_trends(user_id, metric, period)
        
        return {
            "success": True,
            "message": "Trend analysis completed",
            "trends": trends,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error analyzing trends", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze trends"
        )


@router.get("/status", response_model=HealthCheckResponse)
async def health_check():
    """System health check endpoint."""
    try:
        health_checker = get_health_checker()
        system_health = health_checker.check_system_health()
        
        # Get assistant health
        assistant = get_assistant()
        assistant_health = health_checker.check_ai_assistant_health(assistant)
        
        # Combine health statuses
        components = {
            **system_health["components"],
            **assistant_health["components"]
        }
        
        # Determine overall status
        overall_status = "healthy"
        if any(status == "critical" for status in components.values()):
            overall_status = "critical"
        elif any(status == "warning" for status in components.values()):
            overall_status = "warning"
        
        settings = get_settings()
        
        return HealthCheckResponse(
            status=overall_status,
            components=components,
            version=settings.app_version,
            environment=settings.environment
        )
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return HealthCheckResponse(
            status="error",
            components={"system": "error"},
            version="unknown",
            environment="unknown"
        )


# Helper functions for data fetching and analysis
async def _fetch_health_data(
    user_id: str,
    data_types: List[str],
    date_from: Optional[str],
    date_to: Optional[str]
) -> Dict[str, Any]:
    """Fetch health data from various sources."""
    # In a real implementation, this would fetch from Fitbit API, database, etc.
    # For now, we'll return mock data
    
    # Load mock data
    import os
    mock_data_path = os.path.join("data", "mock_user_data.json")
    
    if os.path.exists(mock_data_path):
        with open(mock_data_path, 'r') as f:
            mock_data = json.load(f)
    else:
        # Fallback mock data
        mock_data = {
            "blood_pressure": {
                "latest": {"systolic": 128, "diastolic": 82, "timestamp": datetime.now().isoformat()},
                "trend": "improving",
                "weekly_avg": {"systolic": 132, "diastolic": 85, "timestamp": datetime.now().isoformat()}
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
    
    return {
        "blood_pressure": mock_data.get("blood_pressure"),
        "heart_rate": mock_data.get("heart_rate"),
        "activity": mock_data.get("steps"),
        "sleep": mock_data.get("sleep"),
        "trends": {},
        "insights": []
    }


async def _fetch_blood_pressure_data(user_id: str, days: int) -> Dict[str, Any]:
    """Fetch blood pressure data."""
    # Mock implementation
    return {
        "user_id": user_id,
        "latest": {"systolic": 128, "diastolic": 82, "timestamp": datetime.now().isoformat()},
        "trend": "improving",
        "weekly_avg": {"systolic": 132, "diastolic": 85},
        "daily_readings": [
            {"systolic": 130, "diastolic": 84, "timestamp": datetime.now().isoformat()},
            {"systolic": 128, "diastolic": 82, "timestamp": datetime.now().isoformat()}
        ]
    }


async def _fetch_activity_data(user_id: str, days: int) -> Dict[str, Any]:
    """Fetch activity data."""
    # Mock implementation
    return {
        "user_id": user_id,
        "today": {"steps": 6500, "calories": 2100, "active_minutes": 45},
        "weekly_total": {"steps": 41000, "calories": 14700, "active_minutes": 315},
        "goals": {"daily_steps": 10000, "daily_calories": 2500, "daily_active_minutes": 60},
        "trends": {"steps_trend": "increasing", "calories_trend": "stable"}
    }


async def _fetch_sleep_data(user_id: str, days: int) -> Dict[str, Any]:
    """Fetch sleep data."""
    # Mock implementation
    return {
        "user_id": user_id,
        "last_night": {"hours": 7.2, "quality_score": 78, "deep_sleep": 2.1, "rem_sleep": 1.8},
        "weekly_avg": {"hours": 6.8, "quality_score": 75},
        "sleep_schedule": {"bedtime": "23:00", "wake_time": "07:00"},
        "trends": {"sleep_duration": "improving", "sleep_quality": "stable"}
    }


async def _fetch_heart_rate_data(user_id: str, days: int) -> Dict[str, Any]:
    """Fetch heart rate data."""
    # Mock implementation
    return {
        "user_id": user_id,
        "resting_avg": 68,
        "active_avg": 120,
        "hrv": {"current": 45, "weekly_avg": 42, "trend": "improving"},
        "zones": {
            "rest": {"min": 60, "max": 100, "time": 1200},
            "fat_burn": {"min": 100, "max": 140, "time": 300},
            "cardio": {"min": 140, "max": 170, "time": 150}
        }
    }


async def _analyze_trends(health_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze health data trends."""
    # Mock trend analysis
    return {
        "blood_pressure": {"trend": "improving", "confidence": 0.85},
        "activity": {"trend": "increasing", "confidence": 0.90},
        "sleep": {"trend": "stable", "confidence": 0.75},
        "heart_rate": {"trend": "improving", "confidence": 0.80}
    }


async def _generate_insights(health_data: Dict[str, Any]) -> List[str]:
    """Generate health insights."""
    insights = []
    
    # Blood pressure insights
    if health_data.get("blood_pressure"):
        bp = health_data["blood_pressure"]
        if bp.get("trend") == "improving":
            insights.append("Your blood pressure is showing positive trends. Keep up the good work!")
    
    # Activity insights
    if health_data.get("activity"):
        activity = health_data["activity"]
        if activity.get("today", {}).get("steps", 0) < 8000:
            insights.append("You're below your daily step goal. Consider a short walk!")
    
    # Sleep insights
    if health_data.get("sleep"):
        sleep = health_data["sleep"]
        if sleep.get("last_night", {}).get("hours", 0) < 7:
            insights.append("You got less sleep than recommended. Try to get 7-9 hours tonight.")
    
    return insights


async def _generate_personalized_insights(
    user_id: str,
    insight_type: Optional[str],
    assistant
) -> List[Dict[str, Any]]:
    """Generate personalized health insights."""
    # Mock personalized insights
    insights = [
        {
            "type": "activity",
            "title": "Great Progress on Steps!",
            "message": "You've increased your daily steps by 15% this week.",
            "priority": "high",
            "actionable": True,
            "suggested_actions": ["Keep up the walking routine", "Try adding some jogging"]
        },
        {
            "type": "sleep",
            "title": "Sleep Quality Improving",
            "message": "Your sleep quality has improved by 10% over the past week.",
            "priority": "medium",
            "actionable": False,
            "suggested_actions": []
        },
        {
            "type": "blood_pressure",
            "title": "Blood Pressure in Healthy Range",
            "message": "Your blood pressure readings are consistently in the healthy range.",
            "priority": "low",
            "actionable": False,
            "suggested_actions": []
        }
    ]
    
    # Filter by type if specified
    if insight_type:
        insights = [insight for insight in insights if insight["type"] == insight_type]
    
    return insights


async def _analyze_health_trends(
    user_id: str,
    metric: str,
    period: str
) -> Dict[str, Any]:
    """Analyze trends for a specific health metric."""
    # Mock trend analysis
    return {
        "metric": metric,
        "period": period,
        "trend": "improving",
        "change_percentage": 12.5,
        "confidence": 0.85,
        "data_points": [
            {"date": "2024-01-10", "value": 125},
            {"date": "2024-01-11", "value": 128},
            {"date": "2024-01-12", "value": 126}
        ],
        "recommendations": [
            "Continue current routine",
            "Monitor for any changes",
            "Consider additional exercise"
        ]
    } 