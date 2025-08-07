"""
FastAPI application for Hello Heart AI Assistant.

This module provides the main API interface with comprehensive endpoints
for health data analysis, conversational AI, and user management.
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import structlog
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from app.core.config import get_settings, setup_logging
from app.orchestration.workflow import HealthAIAssistant
from app.models.schemas import (
    ChatRequest, ChatResponse, HealthDataRequest, HealthDataResponse,
    UserProfile, SystemStatus, ConversationHistory
)
from app.api.dependencies import get_current_user, get_assistant
from app.api.routers import chat, health, users, analytics
from app.core.monitoring import setup_monitoring
from app.core.security import create_access_token, verify_token


# Metrics
REQUEST_COUNT = Counter('hello_heart_requests_total', 'Total requests', ['endpoint', 'method'])
REQUEST_LATENCY = Histogram('hello_heart_request_duration_seconds', 'Request latency', ['endpoint'])

# Security
security = HTTPBearer()

# Structured logging
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Hello Heart AI Assistant", version=get_settings().app_version)
    setup_logging()
    setup_monitoring()
    
    # Initialize assistant
    try:
        assistant = HealthAIAssistant()
        app.state.assistant = assistant
        logger.info("Health AI Assistant initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize Health AI Assistant", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Hello Heart AI Assistant")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="Hello Heart AI Assistant",
        description="Advanced conversational AI for personalized health insights and monitoring",
        version=settings.app_version,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan
    )
    
    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
    
    # Add custom middleware for metrics and logging
    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(
            "Incoming request",
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else None
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Record metrics
        REQUEST_COUNT.labels(
            endpoint=request.url.path,
            method=request.method
        ).inc()
        
        REQUEST_LATENCY.labels(
            endpoint=request.url.path
        ).observe(duration)
        
        # Log response
        logger.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            duration=duration
        )
        
        return response
    
    # Include routers
    app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
    app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
    app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
    app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
    
    # Root endpoint
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint with system information."""
        return {
            "app": "Hello Heart AI Assistant",
            "version": settings.app_version,
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "environment": settings.environment
        }
    
    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        """Health check endpoint."""
        try:
            assistant = getattr(app.state, 'assistant', None)
            if assistant:
                status_info = assistant.get_system_status()
                return {
                    "status": "healthy",
                    "assistant": status_info,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "degraded",
                    "message": "Assistant not initialized",
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service unavailable"
            )
    
    # Metrics endpoint
    @app.get("/metrics", tags=["monitoring"])
    async def metrics():
        """Prometheus metrics endpoint."""
        return JSONResponse(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
    
    # Error handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions."""
        logger.warning(
            "HTTP exception",
            status_code=exc.status_code,
            detail=exc.detail,
            url=str(request.url)
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail, "timestamp": datetime.now().isoformat()}
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions."""
        logger.error(
            "Unhandled exception",
            error=str(exc),
            url=str(request.url),
            exc_info=True
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "timestamp": datetime.now().isoformat()
            }
        )
    
    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    
    uvicorn.run(
        "app.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    ) 