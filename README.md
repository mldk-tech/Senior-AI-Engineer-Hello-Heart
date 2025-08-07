# Hello Heart AI Assistant

A production-ready conversational AI assistant for personalized health insights and monitoring, specifically designed for www.helloheart.com.

## 🚀 Features

### Core AI Capabilities
- **Multi-Agent Architecture**: Intent classification, data retrieval, response generation, safety checks, and proactive engagement
- **Conversational AI**: Natural language processing with context awareness
- **Health Data Integration**: Blood pressure, heart rate, activity, and sleep monitoring
- **Personalized Insights**: AI-generated health recommendations and trend analysis
- **Safety & Compliance**: Medical disclaimers, emergency detection, and safety protocols

### Production Features
- **FastAPI REST API**: High-performance async API with comprehensive endpoints
- **Authentication & Security**: JWT tokens, password hashing, rate limiting
- **Monitoring & Observability**: Prometheus metrics, structured logging, health checks
- **Caching & Performance**: Redis caching, response optimization
- **Scalability**: Microservices-ready architecture with containerization support

### Health & Wellness
- **Real-time Health Monitoring**: Integration with Fitbit and other health devices
- **Proactive Engagement**: Smart nudges and reminders
- **Trend Analysis**: AI-powered health trend detection
- **Goal Tracking**: Personalized health goal management
- **Emergency Detection**: Automatic escalation for health emergencies

## 🏗️ Architecture

```
hello_heart_ai/
├── app/
│   ├── api/                    # FastAPI application
│   │   ├── main.py            # Main API entry point
│   │   ├── schemas.py         # Pydantic models
│   │   ├── dependencies.py    # Dependency injection
│   │   └── routers/           # API route handlers
│   │       ├── chat.py        # Chat endpoints
│   │       ├── health.py      # Health data endpoints
│   │       ├── users.py       # User management
│   │       └── analytics.py   # Analytics & reporting
│   ├── agents/                # AI agents
│   │   ├── base.py           # Base agent class
│   │   ├── intent.py         # Intent classification
│   │   ├── data.py           # Data retrieval
│   │   ├── response.py       # Response generation
│   │   ├── safety.py         # Safety checks
│   │   ├── followup.py       # Follow-up logic
│   │   └── rag.py            # RAG implementation
│   ├── core/                 # Core functionality
│   │   ├── config.py         # Configuration management
│   │   ├── security.py       # Security utilities
│   │   └── monitoring.py     # Monitoring & metrics
│   ├── models/               # Data models
│   │   └── schemas.py        # Pydantic schemas
│   └── orchestration/        # Workflow orchestration
│       └── workflow.py       # LangGraph workflow
├── data/                     # Mock data and resources
├── tests/                    # Test suite
└── requirements.txt          # Dependencies
```

## 🛠️ Installation

### Prerequisites
- Python 3.9+
- Redis 6.0+
- PostgreSQL 13+ (optional for production)

### Quick Start

1. **Clone the repository**
```bash
git clone <repository-url>
cd hello-heart
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp hello_heart_ai/env.example hello_heart_ai/.env
# Edit .env with your configuration
```

5. **Start Redis**
```bash
# Using Docker
docker run -d -p 6379:6379 redis:latest

# Or install locally
# Follow Redis installation guide for your OS
```

6. **Run the application**
```bash
# Development mode
cd hello_heart_ai
python -m uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

## 🔧 Configuration

### Environment Variables

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_PREFIX=/api/v1

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.5
OPENAI_MAX_TOKENS=500

# Anthropic Configuration
ANTHROPIC_API_KEY=your-anthropic-api-key
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# Database Configuration
DATABASE_URL=postgresql://user:pass@localhost/helloheart
REDIS_URL=redis://localhost:6379/0

# Security Configuration
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Monitoring Configuration
ENABLE_METRICS=true
METRICS_PORT=9090
SENTRY_DSN=your-sentry-dsn

# External Integrations
FITBIT_CLIENT_ID=your-fitbit-client-id
FITBIT_CLIENT_SECRET=your-fitbit-client-secret
APPLE_HEALTHKIT_ENABLED=false

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,https://www.helloheart.com
```

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Authentication
All protected endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

### Key Endpoints

#### Chat API
```bash
# Send a message
POST /chat/send
{
  "user_id": "user123",
  "message": "How did I sleep last night?",
  "conversation_id": "optional-conversation-id"
}

# Get conversation history
GET /chat/conversations/{conversation_id}?user_id={user_id}

# Get chat suggestions
GET /chat/suggestions?user_id={user_id}&context={context}
```

#### Health Data API
```bash
# Get comprehensive health data
GET /health/data/{user_id}?data_types=blood_pressure,activity,sleep

# Get blood pressure data
GET /health/blood-pressure/{user_id}?days=7

# Get activity data
GET /health/activity/{user_id}?days=7

# Get sleep data
GET /health/sleep/{user_id}?days=7

# Get health insights
GET /health/insights/{user_id}?insight_type=activity
```

#### User Management API
```bash
# Register user
POST /users/register
{
  "email": "user@example.com",
  "password": "securepassword",
  "name": "John Doe",
  "age": 30,
  "gender": "male",
  "health_goals": ["lower_blood_pressure", "increase_activity"]
}

# Login user
POST /users/login
{
  "email": "user@example.com",
  "password": "securepassword"
}

# Get user profile
GET /users/profile

# Update user profile
PUT /users/profile
{
  "name": "John Doe",
  "age": 31,
  "health_goals": ["lower_blood_pressure", "improve_sleep"]
}
```

#### Analytics API
```bash
# Get user dashboard
GET /analytics/dashboard/{user_id}?period=7d

# Get health summary
GET /analytics/health-summary/{user_id}?days=30

# Get progress analysis
GET /analytics/progress/{user_id}?goal_type=steps&timeframe=month

# Get personalized recommendations
GET /analytics/recommendations/{user_id}?category=activity
```

## 🤖 AI Assistant Usage

### Interactive Mode
```bash
cd hello_heart_ai
python -m app.main interactive
```

### Demo Mode
```bash
cd hello_heart_ai
python -m app.main demo
```

### Example Conversations

**User**: "How did I sleep last night?"
**Assistant**: "Based on your sleep data, you slept for 7.2 hours with a quality score of 78. This is within the recommended range of 7-9 hours. Your sleep quality has improved by 10% compared to last week. Keep up the good work!"

**User**: "Am I meeting my activity goals?"
**Assistant**: "You've taken 6,500 steps today, which is 65% of your daily goal of 10,000 steps. You're on track to meet your weekly goal with 41,000 steps out of 49,000. Consider a 20-minute walk this evening to reach your daily target."

**User**: "What's my blood pressure trend?"
**Assistant**: "Your blood pressure is showing positive trends! Your latest reading is 128/82, which is in the healthy range. Over the past week, your average has been 132/85, showing improvement. Continue your current routine and monitor weekly."

## 🔍 Monitoring & Observability

### Health Checks
```bash
# System health
GET /health

# Metrics endpoint
GET /metrics
```

### Key Metrics
- Request count and latency
- Assistant response times and confidence scores
- Health data cache hit ratios
- User engagement metrics
- Safety flag counts
- System resource usage

### Logging
Structured JSON logging with correlation IDs for request tracing.

## 🧪 Testing

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_chat.py
```

### Test Examples
```python
# Test chat functionality
def test_chat_message():
    response = client.post("/api/v1/chat/send", json={
        "user_id": "test_user",
        "message": "How did I sleep?"
    })
    assert response.status_code == 200
    assert "sleep" in response.json()["response"].lower()
```

## 🚀 Deployment

### Docker Deployment
```bash
# Build image
docker build -t hello-heart-ai .

# Run container
docker run -p 8000:8000 -p 9090:9090 hello-heart-ai
```

### Docker Compose
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
      - "9090:9090"
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
      - postgres
  
  redis:
    image: redis:latest
    ports:
      - "6379:6379"
  
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: helloheart
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    ports:
      - "5432:5432"
```

### Production Considerations
- Use environment-specific configurations
- Set up proper SSL/TLS certificates
- Configure load balancers
- Set up monitoring and alerting
- Implement proper backup strategies
- Use managed Redis and PostgreSQL services

## 🔐 Security

### Authentication
- JWT-based authentication
- Password hashing with bcrypt
- Token expiration and refresh
- Rate limiting per user

### Data Protection
- Input sanitization
- SQL injection prevention
- XSS protection
- CORS configuration
- Health data encryption

### Compliance
- HIPAA-compliant data handling
- Medical disclaimers
- Emergency escalation protocols
- Audit logging

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add type hints to all functions
- Write comprehensive docstrings
- Include unit tests for new features
- Update documentation as needed

## 📄 License

This project is licensed under the AGPL-3.0 License - see the LICENSE file for details.

## 🆘 Support

### Documentation
- API documentation available at `/docs` when running in debug mode
- Interactive API explorer at `/redoc`

### Issues
- Report bugs via GitHub Issues
- Include detailed reproduction steps
- Provide system information and logs

### Contact
- Email: support@helloheart.com
- Website: https://www.helloheart.com

## 🎯 Roadmap

### Phase 1 (Current)
- ✅ Multi-agent AI architecture
- ✅ FastAPI REST API
- ✅ Health data integration
- ✅ Basic monitoring

### Phase 2 (Next)
- 🔄 Advanced RAG implementation
- 🔄 Real-time health device integration
- 🔄 Advanced analytics dashboard
- 🔄 Mobile app integration

### Phase 3 (Future)
- 📋 Clinical validation
- 📋 Multi-modal input (voice, image)
- 📋 Advanced personalization
- 📋 Integration with healthcare providers

---

**Hello Heart AI Assistant** - Empowering users with AI-driven health insights and personalized wellness guidance.
