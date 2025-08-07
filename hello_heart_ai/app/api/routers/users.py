"""
Users router for Hello Heart AI Assistant API.

This module provides endpoints for user management, authentication,
and profile operations.
"""

import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
import structlog

from app.api.schemas import (
    UserProfile, UserRegistration, UserLogin, UserAuthResponse,
    BaseResponse
)
from app.api.dependencies import (
    get_current_user, get_optional_user, get_redis,
    get_user_preferences, save_user_preferences, rate_limit
)
from app.core.security import (
    get_password_hash, verify_password, create_user_token,
    validate_email, check_password_strength
)
from app.core.monitoring import get_metrics_collector

# Structured logging
logger = structlog.get_logger()

# Create router
router = APIRouter()


@router.post("/register", response_model=UserAuthResponse)
@rate_limit(requests_per_minute=5, requests_per_hour=20)
async def register_user(
    registration: UserRegistration,
    redis_conn = Depends(get_redis)
):
    """Register a new user."""
    try:
        # Validate email
        if not validate_email(registration.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        
        # Check password strength
        password_analysis = check_password_strength(registration.password)
        if not password_analysis["is_acceptable"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password too weak: {', '.join(password_analysis['feedback'])}"
            )
        
        # Check if user already exists (in a real app, this would check database)
        existing_user_key = f"user:{registration.email}"
        existing_user = await redis_conn.get(existing_user_key)
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists"
            )
        
        # Create user profile
        user_id = f"user_{int(time.time())}"
        hashed_password = get_password_hash(registration.password)
        
        user_profile = UserProfile(
            user_id=user_id,
            email=registration.email,
            name=registration.name,
            age=registration.age,
            gender=registration.gender,
            health_goals=registration.health_goals,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Store user data in Redis
        user_data = {
            "user_id": user_id,
            "email": registration.email,
            "hashed_password": hashed_password,
            "profile": user_profile.dict()
        }
        
        import json
        await redis_conn.setex(
            existing_user_key,
            86400 * 30,  # 30 days TTL
            json.dumps(user_data)
        )
        
        # Create access token
        access_token = create_user_token(
            user_id=user_id,
            email=registration.email,
            additional_data={
                "name": registration.name,
                "age": registration.age,
                "gender": registration.gender,
                "health_goals": registration.health_goals
            }
        )
        
        # Record metrics
        metrics_collector = get_metrics_collector()
        metrics_collector.record_user_interaction(user_id, "user_registered")
        
        logger.info(
            "User registered successfully",
            user_id=user_id,
            email=registration.email
        )
        
        return UserAuthResponse(
            success=True,
            message="User registered successfully",
            access_token=access_token,
            token_type="bearer",
            expires_in=1800,  # 30 minutes
            user_profile=user_profile
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error registering user", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user"
        )


@router.post("/login", response_model=UserAuthResponse)
@rate_limit(requests_per_minute=10, requests_per_hour=50)
async def login_user(
    login: UserLogin,
    redis_conn = Depends(get_redis)
):
    """Login user."""
    try:
        # Find user by email
        user_key = f"user:{login.email}"
        user_data = await redis_conn.get(user_key)
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        import json
        user_info = json.loads(user_data)
        
        # Verify password
        if not verify_password(login.password, user_info["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Create access token
        access_token = create_user_token(
            user_id=user_info["user_id"],
            email=login.email,
            additional_data=user_info["profile"]
        )
        
        # Create user profile
        user_profile = UserProfile(**user_info["profile"])
        
        # Record metrics
        metrics_collector = get_metrics_collector()
        metrics_collector.record_user_interaction(user_info["user_id"], "user_logged_in")
        
        logger.info(
            "User logged in successfully",
            user_id=user_info["user_id"],
            email=login.email
        )
        
        return UserAuthResponse(
            success=True,
            message="Login successful",
            access_token=access_token,
            token_type="bearer",
            expires_in=1800,  # 30 minutes
            user_profile=user_profile
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error during login", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to login"
        )


@router.get("/profile", response_model=UserProfile)
async def get_user_profile(
    current_user = Depends(get_current_user)
):
    """Get current user's profile."""
    try:
        return current_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting user profile", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user profile"
        )


@router.put("/profile", response_model=UserProfile)
async def update_user_profile(
    profile_update: UserProfile,
    current_user = Depends(get_current_user),
    redis_conn = Depends(get_redis)
):
    """Update user profile."""
    try:
        # Update profile fields
        updated_profile = current_user.copy(update=profile_update.dict(exclude_unset=True))
        updated_profile.updated_at = datetime.now()
        
        # Store updated profile in Redis
        user_key = f"user:{current_user.email}"
        user_data = await redis_conn.get(user_key)
        
        if user_data:
            import json
            user_info = json.loads(user_data)
            user_info["profile"] = updated_profile.dict()
            
            await redis_conn.setex(
                user_key,
                86400 * 30,  # 30 days TTL
                json.dumps(user_info)
            )
        
        # Record metrics
        metrics_collector = get_metrics_collector()
        metrics_collector.record_user_interaction(current_user.user_id, "profile_updated")
        
        logger.info(
            "User profile updated",
            user_id=current_user.user_id,
            email=current_user.email
        )
        
        return updated_profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating user profile", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )


@router.get("/preferences")
async def get_user_preferences_endpoint(
    current_user = Depends(get_current_user),
    redis_conn = Depends(get_redis)
):
    """Get user preferences."""
    try:
        preferences = await get_user_preferences(current_user.user_id, redis_conn)
        
        return {
            "success": True,
            "message": "Preferences retrieved successfully",
            "preferences": preferences
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting user preferences", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user preferences"
        )


@router.put("/preferences")
async def update_user_preferences(
    preferences: Dict[str, Any],
    current_user = Depends(get_current_user),
    redis_conn = Depends(get_redis)
):
    """Update user preferences."""
    try:
        success = await save_user_preferences(current_user.user_id, preferences, redis_conn)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save preferences"
            )
        
        # Record metrics
        metrics_collector = get_metrics_collector()
        metrics_collector.record_user_interaction(current_user.user_id, "preferences_updated")
        
        logger.info(
            "User preferences updated",
            user_id=current_user.user_id
        )
        
        return {
            "success": True,
            "message": "Preferences updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating user preferences", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences"
        )


@router.post("/logout")
async def logout_user(
    current_user = Depends(get_current_user)
):
    """Logout user (invalidate token)."""
    try:
        # In a real implementation, you would add the token to a blacklist
        # For now, we'll just return success
        
        # Record metrics
        metrics_collector = get_metrics_collector()
        metrics_collector.record_user_interaction(current_user.user_id, "user_logged_out")
        
        logger.info(
            "User logged out",
            user_id=current_user.user_id,
            email=current_user.email
        )
        
        return {
            "success": True,
            "message": "Logout successful"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error during logout", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to logout"
        )


@router.delete("/account")
async def delete_user_account(
    current_user = Depends(get_current_user),
    redis_conn = Depends(get_redis)
):
    """Delete user account."""
    try:
        # Delete user data from Redis
        user_key = f"user:{current_user.email}"
        await redis_conn.delete(user_key)
        
        # Delete user preferences
        preferences_key = f"user_preferences:{current_user.user_id}"
        await redis_conn.delete(preferences_key)
        
        # Record metrics
        metrics_collector = get_metrics_collector()
        metrics_collector.record_user_interaction(current_user.user_id, "account_deleted")
        
        logger.info(
            "User account deleted",
            user_id=current_user.user_id,
            email=current_user.email
        )
        
        return {
            "success": True,
            "message": "Account deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting user account", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account"
        )


@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user = Depends(get_current_user),
    redis_conn = Depends(get_redis)
):
    """Change user password."""
    try:
        # Get user data
        user_key = f"user:{current_user.email}"
        user_data = await redis_conn.get(user_key)
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        import json
        user_info = json.loads(user_data)
        
        # Verify current password
        if not verify_password(current_password, user_info["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Check new password strength
        password_analysis = check_password_strength(new_password)
        if not password_analysis["is_acceptable"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"New password too weak: {', '.join(password_analysis['feedback'])}"
            )
        
        # Update password
        new_hashed_password = get_password_hash(new_password)
        user_info["hashed_password"] = new_hashed_password
        
        await redis_conn.setex(
            user_key,
            86400 * 30,  # 30 days TTL
            json.dumps(user_info)
        )
        
        # Record metrics
        metrics_collector = get_metrics_collector()
        metrics_collector.record_user_interaction(current_user.user_id, "password_changed")
        
        logger.info(
            "User password changed",
            user_id=current_user.user_id,
            email=current_user.email
        )
        
        return {
            "success": True,
            "message": "Password changed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error changing password", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.get("/stats")
async def get_user_stats(
    current_user = Depends(get_current_user),
    redis_conn = Depends(get_redis)
):
    """Get user statistics."""
    try:
        # In a real implementation, this would aggregate data from various sources
        # For now, we'll return mock statistics
        
        stats = {
            "total_conversations": 15,
            "total_messages": 127,
            "health_data_points": 234,
            "days_active": 23,
            "last_activity": datetime.now().isoformat(),
            "favorite_topics": ["blood pressure", "sleep", "activity"],
            "engagement_score": 0.85
        }
        
        return {
            "success": True,
            "message": "User statistics retrieved successfully",
            "stats": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting user stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user statistics"
        ) 