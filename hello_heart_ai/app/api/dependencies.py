"""
FastAPI dependencies for Hello Heart AI Assistant.

This module provides dependency injection functions for:
- Redis connections (replaced with in-memory storage for POC)
- User authentication
- Rate limiting
- Conversation context management
- User preferences
"""

import time
from typing import Dict, Any, Optional
from functools import wraps
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError

from app.core.config import get_settings
from app.core.security import verify_token
from app.orchestration.workflow import HealthAIAssistant
from app.models.schemas import UserProfile, RateLimitInfo

# Security
security = HTTPBearer()

# In-memory storage for POC (replaces Redis)
in_memory_storage = {
    "conversations": {},
    "user_preferences": {},
    "rate_limits": {},
    "health_data_cache": {}
}

# Rate limiting storage
rate_limit_data = {}


async def get_assistant() -> HealthAIAssistant:
    """Get the health assistant instance."""
    # This would typically be injected via FastAPI's dependency injection
    # For now, we'll create a new instance
    return HealthAIAssistant()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserProfile:
    """Get current authenticated user."""
    try:
        settings = get_settings()
        payload = verify_token(credentials.credentials, settings.secret_key)
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # In a real application, you would fetch user from database
        # For now, we'll create a mock user profile
        user_profile = UserProfile(
            user_id=user_id,
            email=payload.get("email"),
            name=payload.get("name"),
            age=payload.get("age"),
            gender=payload.get("gender"),
            health_goals=payload.get("health_goals", []),
            preferences=payload.get("preferences", {})
        )
        
        return user_profile
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    request: Request
) -> Optional[UserProfile]:
    """Get current user if authenticated, otherwise None."""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.split(" ")[1]
        settings = get_settings()
        payload = verify_token(token, settings.secret_key)
        user_id: str = payload.get("sub")
        
        if user_id is None:
            return None
        
        # Create mock user profile
        user_profile = UserProfile(
            user_id=user_id,
            email=payload.get("email"),
            name=payload.get("name"),
            age=payload.get("age"),
            gender=payload.get("gender"),
            health_goals=payload.get("health_goals", []),
            preferences=payload.get("preferences", {})
        )
        
        return user_profile
        
    except (JWTError, IndexError):
        return None


def rate_limit(
    requests_per_minute: int = 60,
    requests_per_hour: int = 1000
):
    """Rate limiting decorator."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request') or args[0] if args else None
            if not request:
                return await func(*args, **kwargs)
            
            # Get client IP for rate limiting
            client_ip = request.client.host
            current_time = time.time()
            
            # Initialize rate limit data for this client
            if client_ip not in rate_limit_data:
                rate_limit_data[client_ip] = {
                    'minute_requests': [],
                    'hour_requests': []
                }
            
            # Clean old requests
            minute_ago = current_time - 60
            hour_ago = current_time - 3600
            
            rate_limit_data[client_ip]['minute_requests'] = [
                req_time for req_time in rate_limit_data[client_ip]['minute_requests']
                if req_time > minute_ago
            ]
            rate_limit_data[client_ip]['hour_requests'] = [
                req_time for req_time in rate_limit_data[client_ip]['hour_requests']
                if req_time > hour_ago
            ]
            
            # Check limits
            if len(rate_limit_data[client_ip]['minute_requests']) >= requests_per_minute:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded for minute"
                )
            
            if len(rate_limit_data[client_ip]['hour_requests']) >= requests_per_hour:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded for hour"
                )
            
            # Add current request
            rate_limit_data[client_ip]['minute_requests'].append(current_time)
            rate_limit_data[client_ip]['hour_requests'].append(current_time)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


async def get_rate_limit_info(user_id: str) -> RateLimitInfo:
    """Get rate limit information for a user."""
    current_time = time.time()
    minute_ago = current_time - 60
    hour_ago = current_time - 3600
    
    # Count requests in time windows
    minute_requests = sum(1 for req_time in rate_limit_data.get(user_id, {}).get('minute_requests', [])
                         if req_time > minute_ago)
    hour_requests = sum(1 for req_time in rate_limit_data.get(user_id, {}).get('hour_requests', [])
                       if req_time > hour_ago)
    
    return RateLimitInfo(
        requests_per_minute=minute_requests,
        requests_per_hour=hour_requests,
        limit_per_minute=60,
        limit_per_hour=1000
    )


async def validate_health_data_access(
    user_id: str,
    data_type: str,
    current_user: UserProfile = Depends(get_current_user)
) -> bool:
    """Validate user access to health data."""
    # For POC, allow access if user is authenticated
    return current_user.user_id == user_id


async def get_conversation_context(
    conversation_id: str,
    user_id: str
) -> Dict[str, Any]:
    """Get conversation context from in-memory storage."""
    key = f"{user_id}:{conversation_id}"
    return in_memory_storage["conversations"].get(key, {
        "messages": [],
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
    })


async def save_conversation_context(
    conversation_id: str,
    user_id: str,
    context: Dict[str, Any]
) -> bool:
    """Save conversation context to in-memory storage."""
    try:
        key = f"{user_id}:{conversation_id}"
        context["metadata"]["last_updated"] = datetime.now().isoformat()
        in_memory_storage["conversations"][key] = context
        return True
    except Exception:
        return False


async def get_user_preferences(
    user_id: str
) -> Dict[str, Any]:
    """Get user preferences from in-memory storage."""
    return in_memory_storage["user_preferences"].get(user_id, {
        "notifications_enabled": True,
        "daily_reminders": True,
        "weekly_reports": True,
        "health_goals": [],
        "privacy_settings": {
            "share_data": False,
            "anonymous_analytics": True
        }
    })


async def save_user_preferences(
    user_id: str,
    preferences: Dict[str, Any]
) -> bool:
    """Save user preferences to in-memory storage."""
    try:
        in_memory_storage["user_preferences"][user_id] = preferences
        return True
    except Exception:
        return False


async def get_cached_health_data(
    user_id: str,
    data_type: str
) -> Optional[Dict[str, Any]]:
    """Get cached health data from in-memory storage."""
    key = f"{user_id}:{data_type}"
    cached_data = in_memory_storage["health_data_cache"].get(key)
    
    if cached_data:
        # Check if cache is still valid (5 minutes)
        cache_time = datetime.fromisoformat(cached_data["cached_at"])
        if datetime.now() - cache_time < timedelta(minutes=5):
            return cached_data["data"]
    
    return None


async def cache_health_data(
    user_id: str,
    data_type: str,
    data: Dict[str, Any]
) -> bool:
    """Cache health data in in-memory storage."""
    try:
        key = f"{user_id}:{data_type}"
        in_memory_storage["health_data_cache"][key] = {
            "data": data,
            "cached_at": datetime.now().isoformat()
        }
        return True
    except Exception:
        return False 