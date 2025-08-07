"""
Configuration management for Hello Heart AI Assistant.

This module handles all configuration settings including API keys,
model parameters, and environment-specific settings.
"""

import os
import logging
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application Configuration
    app_name: str = Field(default="Hello Heart AI Assistant", env="APP_NAME")
    app_version: str = Field(default="2.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_prefix: str = Field(default="/api/v1", env="API_PREFIX")
    
    # OpenAI Configuration
    openai_api_key: str = Field(default="mock-api-key", env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")
    openai_temperature: float = Field(default=0.5, env="OPENAI_TEMPERATURE")
    openai_max_tokens: int = Field(default=500, env="OPENAI_MAX_TOKENS")
    openai_top_p: float = Field(default=0.9, env="OPENAI_TOP_P")
    
    # Anthropic Configuration
    anthropic_api_key: str = Field(default="mock-api-key", env="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-3-sonnet-20240229", env="ANTHROPIC_MODEL")
    
    # Database Configuration
    database_url: str = Field(default="postgresql://user:pass@localhost/helloheart", env="DATABASE_URL")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # Health Data Configuration
    mock_data_path: str = Field(
        default="data/mock_user_data.json",
        env="MOCK_DATA_PATH"
    )
    
    # Safety Configuration
    enable_safety_checks: bool = Field(default=True, env="ENABLE_SAFETY_CHECKS")
    emergency_escalation_enabled: bool = Field(
        default=True, 
        env="EMERGENCY_ESCALATION_ENABLED"
    )
    
    # Proactive Engagement Configuration
    max_daily_nudges: int = Field(default=3, env="MAX_DAILY_NUDGES")
    nudge_cooldown_hours: int = Field(default=4, env="NUDGE_COOLDOWN_HOURS")
    
    # Monitoring Configuration
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    
    # Security Configuration
    secret_key: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # External Integrations
    fitbit_client_id: Optional[str] = Field(default=None, env="FITBIT_CLIENT_ID")
    fitbit_client_secret: Optional[str] = Field(default=None, env="FITBIT_CLIENT_SECRET")
    apple_healthkit_enabled: bool = Field(default=False, env="APPLE_HEALTHKIT_ENABLED")
    
    # RAG Configuration
    vector_db_path: str = Field(default="./vector_db", env="VECTOR_DB_PATH")
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_hour: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")
    
    # CORS Configuration
    cors_origins: list = Field(default=["http://localhost:3000", "https://www.helloheart.com"], env="CORS_ORIGINS")
    
    @validator('cors_origins', pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(',')]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


def validate_api_key() -> bool:
    """Validate that a real API key is provided."""
    return (settings.openai_api_key != "mock-api-key" and 
            settings.openai_api_key != "" and
            settings.openai_api_key is not None)


def validate_anthropic_api_key() -> bool:
    """Validate that a real Anthropic API key is provided."""
    return (settings.anthropic_api_key != "mock-api-key" and 
            settings.anthropic_api_key != "" and
            settings.anthropic_api_key is not None)


def setup_logging():
    """Set up logging configuration with structured logging."""
    import structlog
    
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format=settings.log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("hello_heart.log")
        ]
    ) 