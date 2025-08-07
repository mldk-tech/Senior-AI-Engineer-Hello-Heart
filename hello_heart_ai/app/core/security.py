"""
Security utilities for Hello Heart AI Assistant.

This module provides authentication, authorization, and security functions
for the API endpoints.
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from passlib.context import CryptContext
from jose import JWTError, jwt
import structlog

from app.core.config import get_settings

# Structured logging
logger = structlog.get_logger()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token."""
    settings = get_settings()
    
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    
    return encoded_jwt


def verify_token(token: str, secret_key: str) -> Dict[str, Any]:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return payload
    except JWTError as e:
        logger.error("Token verification failed", error=str(e))
        raise


def generate_api_key() -> str:
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(api_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash."""
    return hash_api_key(api_key) == hashed_key


def sanitize_input(input_string: str) -> str:
    """Sanitize user input to prevent injection attacks."""
    import re
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', input_string)
    
    # Limit length
    if len(sanitized) > 1000:
        sanitized = sanitized[:1000]
    
    return sanitized.strip()


def validate_email(email: str) -> bool:
    """Validate email format."""
    import re
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def generate_secure_filename(original_filename: str) -> str:
    """Generate a secure filename."""
    import os
    from datetime import datetime
    
    # Get file extension
    _, ext = os.path.splitext(original_filename)
    
    # Generate secure name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_suffix = secrets.token_hex(8)
    
    return f"{timestamp}_{random_suffix}{ext}"


def check_password_strength(password: str) -> Dict[str, Any]:
    """Check password strength and return detailed analysis."""
    score = 0
    feedback = []
    
    # Length check
    if len(password) >= 8:
        score += 1
    else:
        feedback.append("Password should be at least 8 characters long")
    
    # Uppercase check
    if any(c.isupper() for c in password):
        score += 1
    else:
        feedback.append("Password should contain at least one uppercase letter")
    
    # Lowercase check
    if any(c.islower() for c in password):
        score += 1
    else:
        feedback.append("Password should contain at least one lowercase letter")
    
    # Number check
    if any(c.isdigit() for c in password):
        score += 1
    else:
        feedback.append("Password should contain at least one number")
    
    # Special character check
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if any(c in special_chars for c in password):
        score += 1
    else:
        feedback.append("Password should contain at least one special character")
    
    # Strength classification
    if score <= 2:
        strength = "weak"
    elif score <= 4:
        strength = "medium"
    else:
        strength = "strong"
    
    return {
        "score": score,
        "strength": strength,
        "feedback": feedback,
        "is_acceptable": score >= 3
    }


def create_user_token(
    user_id: str,
    email: str,
    additional_data: Optional[Dict[str, Any]] = None
) -> str:
    """Create a user-specific access token."""
    payload = {
        "sub": user_id,
        "email": email,
        "type": "access"
    }
    
    if additional_data:
        payload.update(additional_data)
    
    return create_access_token(payload)


def create_refresh_token(user_id: str) -> str:
    """Create a refresh token."""
    payload = {
        "sub": user_id,
        "type": "refresh"
    }
    
    # Refresh tokens have longer expiration
    return create_access_token(
        payload,
        expires_delta=timedelta(days=30)
    )


def validate_token_expiration(token: str, secret_key: str) -> bool:
    """Check if token is expired."""
    try:
        payload = verify_token(token, secret_key)
        exp = payload.get("exp")
        
        if exp is None:
            return False
        
        # Check if token is expired
        return datetime.utcnow() < datetime.fromtimestamp(exp)
        
    except JWTError:
        return False


def extract_user_from_token(token: str, secret_key: str) -> Optional[Dict[str, Any]]:
    """Extract user information from token."""
    try:
        payload = verify_token(token, secret_key)
        
        # Check if token is expired
        if not validate_token_expiration(token, secret_key):
            return None
        
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "type": payload.get("type"),
            "additional_data": {k: v for k, v in payload.items() 
                              if k not in ["sub", "email", "type", "exp", "iat"]}
        }
        
    except JWTError:
        return None


def create_session_token(
    user_id: str,
    session_data: Dict[str, Any]
) -> str:
    """Create a session token with additional data."""
    payload = {
        "sub": user_id,
        "type": "session",
        "session_data": session_data
    }
    
    return create_access_token(
        payload,
        expires_delta=timedelta(hours=24)
    )


def validate_session_token(token: str, secret_key: str) -> Optional[Dict[str, Any]]:
    """Validate session token and return session data."""
    try:
        payload = verify_token(token, secret_key)
        
        if payload.get("type") != "session":
            return None
        
        if not validate_token_expiration(token, secret_key):
            return None
        
        return {
            "user_id": payload.get("sub"),
            "session_data": payload.get("session_data", {})
        }
        
    except JWTError:
        return None


def generate_csrf_token() -> str:
    """Generate a CSRF token."""
    return secrets.token_urlsafe(32)


def validate_csrf_token(token: str, stored_token: str) -> bool:
    """Validate CSRF token."""
    return token == stored_token


def create_health_data_token(
    user_id: str,
    data_types: list,
    expiration_hours: int = 1
) -> str:
    """Create a token for accessing health data."""
    payload = {
        "sub": user_id,
        "type": "health_data",
        "data_types": data_types,
        "permissions": ["read"]
    }
    
    return create_access_token(
        payload,
        expires_delta=timedelta(hours=expiration_hours)
    )


def validate_health_data_token(
    token: str,
    secret_key: str,
    required_data_types: Optional[list] = None
) -> Optional[Dict[str, Any]]:
    """Validate health data token and check permissions."""
    try:
        payload = verify_token(token, secret_key)
        
        if payload.get("type") != "health_data":
            return None
        
        if not validate_token_expiration(token, secret_key):
            return None
        
        # Check if required data types are allowed
        if required_data_types:
            allowed_types = payload.get("data_types", [])
            if not all(data_type in allowed_types for data_type in required_data_types):
                return None
        
        return {
            "user_id": payload.get("sub"),
            "data_types": payload.get("data_types", []),
            "permissions": payload.get("permissions", [])
        }
        
    except JWTError:
        return None 