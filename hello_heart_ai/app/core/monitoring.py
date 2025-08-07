"""
Monitoring and observability for Hello Heart AI Assistant.

This module provides comprehensive monitoring, metrics collection,
and health check functionality.
"""

import time
import psutil
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict, deque
import structlog

from prometheus_client import Counter, Histogram, Gauge, Summary, generate_latest
from prometheus_client.exposition import start_http_server

from app.core.config import get_settings

# Structured logging
logger = structlog.get_logger()

# Metrics
REQUEST_COUNT = Counter('hello_heart_requests_total', 'Total requests', ['endpoint', 'method', 'status'])
REQUEST_DURATION = Histogram('hello_heart_request_duration_seconds', 'Request duration', ['endpoint'])
RESPONSE_SIZE = Histogram('hello_heart_response_size_bytes', 'Response size', ['endpoint'])
ERROR_COUNT = Counter('hello_heart_errors_total', 'Total errors', ['endpoint', 'error_type'])

# AI Assistant Metrics
ASSISTANT_REQUESTS = Counter('hello_heart_assistant_requests_total', 'Assistant requests', ['intent', 'safety_level'])
ASSISTANT_RESPONSE_TIME = Histogram('hello_heart_assistant_response_time_seconds', 'Assistant response time', ['intent'])
ASSISTANT_CONFIDENCE = Histogram('hello_heart_assistant_confidence', 'Assistant confidence scores', ['intent'])

# Health Data Metrics
HEALTH_DATA_REQUESTS = Counter('hello_heart_health_data_requests_total', 'Health data requests', ['data_type'])
HEALTH_DATA_CACHE_HITS = Counter('hello_heart_health_data_cache_hits_total', 'Health data cache hits', ['data_type'])
HEALTH_DATA_CACHE_MISSES = Counter('hello_heart_health_data_cache_misses_total', 'Health data cache misses', ['data_type'])

# System Metrics
SYSTEM_MEMORY_USAGE = Gauge('hello_heart_system_memory_bytes', 'System memory usage')
SYSTEM_CPU_USAGE = Gauge('hello_heart_system_cpu_percent', 'System CPU usage')
SYSTEM_DISK_USAGE = Gauge('hello_heart_system_disk_percent', 'System disk usage')

# User Engagement Metrics
USER_SESSIONS = Counter('hello_heart_user_sessions_total', 'User sessions', ['user_id'])
USER_INTERACTIONS = Counter('hello_heart_user_interactions_total', 'User interactions', ['user_id', 'interaction_type'])
USER_RETENTION = Gauge('hello_heart_user_retention_rate', 'User retention rate')

# Conversation Metrics
CONVERSATION_LENGTH = Histogram('hello_heart_conversation_length', 'Conversation length in messages')
CONVERSATION_DURATION = Histogram('hello_heart_conversation_duration_seconds', 'Conversation duration')

# Proactive Engagement Metrics
NUDGE_SENT = Counter('hello_heart_nudges_sent_total', 'Proactive nudges sent', ['nudge_type'])
NUDGE_ENGAGEMENT = Counter('hello_heart_nudge_engagement_total', 'Nudge engagement', ['nudge_type', 'action'])

# Safety Metrics
SAFETY_FLAGS = Counter('hello_heart_safety_flags_total', 'Safety flags raised', ['flag_type', 'severity'])
EMERGENCY_ESCALATIONS = Counter('hello_heart_emergency_escalations_total', 'Emergency escalations')

# Performance Metrics
CACHE_HIT_RATIO = Gauge('hello_heart_cache_hit_ratio', 'Cache hit ratio')
AVERAGE_RESPONSE_TIME = Gauge('hello_heart_average_response_time_seconds', 'Average response time')
ACTIVE_CONNECTIONS = Gauge('hello_heart_active_connections', 'Active connections')

# Custom metrics for business insights
DAILY_ACTIVE_USERS = Gauge('hello_heart_daily_active_users', 'Daily active users')
WEEKLY_ACTIVE_USERS = Gauge('hello_heart_weekly_active_users', 'Weekly active users')
MONTHLY_ACTIVE_USERS = Gauge('hello_heart_monthly_active_users', 'Monthly active users')

# Health check results
HEALTH_CHECK_STATUS = Gauge('hello_heart_health_check_status', 'Health check status', ['component'])


class MetricsCollector:
    """Collector for custom metrics and business insights."""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_times = deque(maxlen=1000)
        self.cache_hits = 0
        self.cache_misses = 0
        self.active_users = set()
        self.daily_users = set()
        self.weekly_users = set()
        self.monthly_users = set()
        
        # Start background monitoring
        self._start_background_monitoring()
    
    def _start_background_monitoring(self):
        """Start background monitoring tasks."""
        def system_monitor():
            while True:
                try:
                    # System metrics
                    memory = psutil.virtual_memory()
                    SYSTEM_MEMORY_USAGE.set(memory.used)
                    SYSTEM_CPU_USAGE.set(psutil.cpu_percent())
                    
                    # Disk usage
                    disk = psutil.disk_usage('/')
                    SYSTEM_DISK_USAGE.set((disk.used / disk.total) * 100)
                    
                    # Cache hit ratio
                    total_cache_requests = self.cache_hits + self.cache_misses
                    if total_cache_requests > 0:
                        hit_ratio = self.cache_hits / total_cache_requests
                        CACHE_HIT_RATIO.set(hit_ratio)
                    
                    # Average response time
                    if self.request_times:
                        avg_time = sum(self.request_times) / len(self.request_times)
                        AVERAGE_RESPONSE_TIME.set(avg_time)
                    
                    time.sleep(60)  # Update every minute
                    
                except Exception as e:
                    logger.error("Error in system monitoring", error=str(e))
                    time.sleep(60)
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=system_monitor, daemon=True)
        monitor_thread.start()
    
    def record_request(self, endpoint: str, method: str, status: int, duration: float, response_size: int = 0):
        """Record request metrics."""
        REQUEST_COUNT.labels(endpoint=endpoint, method=method, status=status).inc()
        REQUEST_DURATION.labels(endpoint=endpoint).observe(duration)
        
        if response_size > 0:
            RESPONSE_SIZE.labels(endpoint=endpoint).observe(response_size)
        
        self.request_times.append(duration)
    
    def record_error(self, endpoint: str, error_type: str):
        """Record error metrics."""
        ERROR_COUNT.labels(endpoint=endpoint, error_type=error_type).inc()
    
    def record_assistant_request(self, intent: str, safety_level: str, response_time: float, confidence: float):
        """Record assistant-specific metrics."""
        ASSISTANT_REQUESTS.labels(intent=intent, safety_level=safety_level).inc()
        ASSISTANT_RESPONSE_TIME.labels(intent=intent).observe(response_time)
        ASSISTANT_CONFIDENCE.labels(intent=intent).observe(confidence)
    
    def record_health_data_request(self, data_type: str, cache_hit: bool):
        """Record health data request metrics."""
        HEALTH_DATA_REQUESTS.labels(data_type=data_type).inc()
        
        if cache_hit:
            HEALTH_DATA_CACHE_HITS.labels(data_type=data_type).inc()
            self.cache_hits += 1
        else:
            HEALTH_DATA_CACHE_MISSES.labels(data_type=data_type).inc()
            self.cache_misses += 1
    
    def record_user_interaction(self, user_id: str, interaction_type: str):
        """Record user interaction metrics."""
        USER_INTERACTIONS.labels(user_id=user_id, interaction_type=interaction_type).inc()
        
        # Track active users
        current_time = time.time()
        self.active_users.add(user_id)
        
        # Daily active users (reset daily)
        if current_time - self.start_time > 86400:  # 24 hours
            self.daily_users.clear()
            self.start_time = current_time
        
        self.daily_users.add(user_id)
        DAILY_ACTIVE_USERS.set(len(self.daily_users))
    
    def record_conversation_metrics(self, message_count: int, duration: float):
        """Record conversation metrics."""
        CONVERSATION_LENGTH.observe(message_count)
        CONVERSATION_DURATION.observe(duration)
    
    def record_nudge_metrics(self, nudge_type: str, action: str = "sent"):
        """Record proactive engagement metrics."""
        NUDGE_SENT.labels(nudge_type=nudge_type).inc()
        NUDGE_ENGAGEMENT.labels(nudge_type=nudge_type, action=action).inc()
    
    def record_safety_metrics(self, flag_type: str, severity: str):
        """Record safety-related metrics."""
        SAFETY_FLAGS.labels(flag_type=flag_type, severity=severity).inc()
    
    def record_emergency_escalation(self):
        """Record emergency escalation."""
        EMERGENCY_ESCALATIONS.inc()
    
    def update_health_check(self, component: str, status: int):
        """Update health check status."""
        HEALTH_CHECK_STATUS.labels(component=component).set(status)


class HealthChecker:
    """Health check functionality."""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.last_checks = {}
    
    def check_system_health(self) -> Dict[str, Any]:
        """Perform comprehensive system health check."""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {},
            "overall_score": 100
        }
        
        # Check system resources
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent()
            disk = psutil.disk_usage('/')
            
            # Memory check
            if memory.percent > 90:
                health_status["components"]["memory"] = "critical"
                health_status["overall_score"] -= 30
            elif memory.percent > 80:
                health_status["components"]["memory"] = "warning"
                health_status["overall_score"] -= 10
            else:
                health_status["components"]["memory"] = "healthy"
            
            # CPU check
            if cpu_percent > 90:
                health_status["components"]["cpu"] = "critical"
                health_status["overall_score"] -= 30
            elif cpu_percent > 80:
                health_status["components"]["cpu"] = "warning"
                health_status["overall_score"] -= 10
            else:
                health_status["components"]["cpu"] = "healthy"
            
            # Disk check
            disk_percent = (disk.used / disk.total) * 100
            if disk_percent > 90:
                health_status["components"]["disk"] = "critical"
                health_status["overall_score"] -= 20
            elif disk_percent > 80:
                health_status["components"]["disk"] = "warning"
                health_status["overall_score"] -= 5
            else:
                health_status["components"]["disk"] = "healthy"
                
        except Exception as e:
            logger.error("Error checking system health", error=str(e))
            health_status["components"]["system"] = "error"
            health_status["overall_score"] -= 50
        
        # Check database connection
        try:
            # For POC, we'll skip database health check
            health_status["components"]["database"] = "not_configured"
        except Exception as e:
            logger.error("Error checking database health", error=str(e))
            health_status["components"]["database"] = "error"

        # Check vector database (FAISS)
        try:
            vector_db_path = settings.vector_db_path
            if os.path.exists(vector_db_path):
                health_status["components"]["vector_db"] = "healthy"
            else:
                health_status["components"]["vector_db"] = "not_initialized"
        except Exception as e:
            logger.error("Error checking vector database health", error=str(e))
            health_status["components"]["vector_db"] = "error"
        
        # Update overall status
        if health_status["overall_score"] < 50:
            health_status["status"] = "critical"
        elif health_status["overall_score"] < 80:
            health_status["status"] = "warning"
        else:
            health_status["status"] = "healthy"
        
        # Update metrics
        for component, status in health_status["components"].items():
            status_value = 1 if status == "healthy" else 0
            self.metrics_collector.update_health_check(component, status_value)
        
        return health_status
    
    def check_ai_assistant_health(self, assistant) -> Dict[str, Any]:
        """Check AI assistant health."""
        try:
            system_status = assistant.get_system_status()
            
            health_status = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "components": {},
                "details": system_status
            }
            
            # Check if all agents are available
            agents = system_status.get("agents", {})
            for agent_name, agent_info in agents.items():
                if agent_info.get("status") == "available":
                    health_status["components"][f"agent_{agent_name}"] = "healthy"
                else:
                    health_status["components"][f"agent_{agent_name}"] = "error"
            
            # Check API key validity
            if system_status.get("api_key_valid", False):
                health_status["components"]["api_key"] = "healthy"
            else:
                health_status["components"]["api_key"] = "warning"
            
            return health_status
            
        except Exception as e:
            logger.error("Error checking AI assistant health", error=str(e))
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "components": {"assistant": "error"},
                "error": str(e)
            }


def setup_monitoring():
    """Set up monitoring and metrics collection."""
    settings = get_settings()
    
    if settings.enable_metrics:
        try:
            # Start Prometheus metrics server
            start_http_server(settings.metrics_port)
            logger.info(f"Metrics server started on port {settings.metrics_port}")
            
            # Initialize health checker
            health_checker = HealthChecker()
            
            # Store in global context for access
            import app.core.monitoring
            app.core.monitoring.health_checker = health_checker
            
            logger.info("Monitoring setup completed successfully")
            
        except Exception as e:
            logger.error("Failed to setup monitoring", error=str(e))


def get_metrics_collector() -> MetricsCollector:
    """Get the metrics collector instance."""
    import app.core.monitoring
    if not hasattr(app.core.monitoring, 'metrics_collector'):
        app.core.monitoring.metrics_collector = MetricsCollector()
    return app.core.monitoring.metrics_collector


def get_health_checker() -> HealthChecker:
    """Get the health checker instance."""
    import app.core.monitoring
    if not hasattr(app.core.monitoring, 'health_checker'):
        app.core.monitoring.health_checker = HealthChecker()
    return app.core.monitoring.health_checker


# Performance monitoring decorator
def monitor_performance(endpoint: str):
    """Decorator to monitor endpoint performance."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Record metrics
                collector = get_metrics_collector()
                collector.record_request(
                    endpoint=endpoint,
                    method="GET",  # Could be made dynamic
                    status=200,
                    duration=duration
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                # Record error metrics
                collector = get_metrics_collector()
                collector.record_request(
                    endpoint=endpoint,
                    method="GET",
                    status=500,
                    duration=duration
                )
                collector.record_error(endpoint, type(e).__name__)
                
                raise
        
        return wrapper
    return decorator 