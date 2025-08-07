# Hello Heart AI Assistant

A production-grade conversational AI health assistant built with LangGraph, OpenAI, FAISS, and Pydantic.

## 🏗️ Architecture

The project follows a modular, production-ready architecture:

```
hello_heart_ai/
├── app/
│   ├── core/           # Configuration and utilities
│   ├── agents/         # Specialized AI agents
│   ├── orchestration/  # Workflow management
│   ├── models/         # Pydantic data models
│   └── main.py         # Application entry point
├── tests/              # Unit and integration tests
├── data/               # Mock data and resources
├── vector_db/          # FAISS vector database storage
└── requirements.txt    # Python dependencies
```

## 🚀 Features

- **Multi-Agent Architecture**: Specialized agents for intent classification, data retrieval, response generation, safety checking, and proactive engagement
- **RAG Integration**: Local sentence-transformers embeddings with FAISS-based Retrieval-Augmented Generation for knowledge queries
- **Persistent State**: Memory checkpointer for conversation state across sessions
- **Safety First**: Built-in medical safety checks and disclaimers
- **Production Ready**: Comprehensive logging, error handling, and configuration management
- **Type Safe**: Full Pydantic integration for data validation
- **Flexible**: Works with or without LangGraph (fallback to sequential processing)
- **Local Embeddings**: Uses sentence-transformers for cost-effective, local embedding generation
- **Local Vector Storage**: FAISS for fast, local vector similarity search

## 📋 Requirements

- Python 3.8+
- OpenAI API key (for LLM responses, optional for demo mode)
- sentence-transformers (for local embeddings)
- FAISS (for local vector storage)

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd hello_heart_ai
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp env.example .env
   # Edit .env with your OpenAI API key
   ```

## 🎯 Usage

### Demo Mode
Run the demonstration scenarios:
```bash
python demo_new_features.py
```

### Test Local Embeddings and FAISS
Test the local sentence-transformers embeddings and FAISS vector store:
```bash
python test_local_embeddings.py
```

### Interactive Mode
Run in interactive conversation mode:
```bash
python -m app.main interactive
```

### System Status
Check system configuration and health:
```bash
python -m app.main status
```

## 🔧 Configuration

The application uses environment variables for configuration. Key settings:

### Embeddings Configuration
```bash
# Local sentence-transformers model for embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Alternative models you can use:
# EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2  # Higher quality
# EMBEDDING_MODEL=sentence-transformers/paraphrase-MiniLM-L6-v2  # Faster
```

### Vector Database Configuration
```bash
# Local FAISS vector database path
VECTOR_DB_PATH=./vector_db
```

## 🏥 Health Assistant Features

### Intent Classification
- Emergency detection
- Knowledge query identification
- Medical advice identification
- Activity and sleep queries
- Blood pressure monitoring

### RAG (Retrieval-Augmented Generation)
- **Knowledge Queries**: Questions about health information, medical concepts, and educational content
- **FAISS Vector Store**: Local semantic search through health knowledge documents
- **Context Enrichment**: Relevant information automatically added to responses
- **Sample Knowledge Base**: Pre-populated with exercise, HRV, blood pressure, sleep, stress, and nutrition information

### Safety Validation
- Medical disclaimer management
- Unsafe content detection
- Emergency response validation

### Proactive Engagement
- Follow-up scheduling
- Personalized nudges
- Progress tracking

### Persistent Conversation State
- **Memory Checkpointer**: Maintains conversation context across sessions
- **Thread Management**: Support for multiple conversation threads
- **State Recovery**: Resume conversations after system restarts

## 🧪 Testing

Run the test suite:
```bash
pytest tests/
```

Test RAG functionality:
```bash
python test_rag_demo.py
```

## 📊 Monitoring

The application includes comprehensive logging and metrics:

- Agent performance metrics
- RAG retrieval statistics
- Safety validation reports
- User engagement analytics
- System health monitoring

## 🔒 Safety & Compliance

- **Medical Disclaimers**: Automatic addition when needed
- **Content Validation**: Regex-based safety checks
- **Emergency Handling**: Proper escalation protocols
- **Data Privacy**: No persistent user data storage
- **Knowledge Attribution**: Source attribution for retrieved information

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For questions or issues, please open an issue on GitHub.

---

**Note**: This is a demonstration system. For production use in healthcare, additional compliance measures and medical oversight are required. 