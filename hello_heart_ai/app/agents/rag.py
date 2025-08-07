"""
FAISS RAG (Retrieval-Augmented Generation) Agent.

This agent retrieves relevant knowledge documents from FAISS vector store
and enhances the conversation context with external information.
"""

import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from langchain_community.vectorstores.faiss import FAISS
    from langchain_core.documents import Document
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    FAISS = None
    Document = None
    SentenceTransformer = None

from app.agents.base import BaseHealthAgent
from app.models.schemas import HealthAssistantState, AgentResponse, Message
from app.core.config import get_settings


class LocalEmbeddings:
    """Local embeddings using sentence-transformers."""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        return self.model.encode(texts).tolist()
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query."""
        return self.model.encode([text])[0].tolist()


class FAISSRAGAgent(BaseHealthAgent):
    """
    RAG Agent that retrieves relevant knowledge from FAISS vector store.
    
    This agent:
    1. Receives a user query
    2. Uses local sentence-transformers to vectorize the query
    3. Searches FAISS Vector Store for similar documents
    4. Appends relevant document content to conversation context
    5. Passes enriched context to ResponseGenerationAgent
    """

    def __init__(self, llm=None):
        super().__init__(llm)
        self.settings = get_settings()
        self.vector_store = None
        self.embeddings = None
        self._initialize_vector_store()

    def _initialize_vector_store(self):
        """Initialize FAISS vector store and local embeddings."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            self.logger.warning("Sentence transformers not available - RAG functionality disabled")
            return

        try:
            # Initialize local embeddings
            self.embeddings = LocalEmbeddings(
                model_name=self.settings.embedding_model
            )

            # Check if FAISS index exists
            faiss_index_path = os.path.join(self.settings.vector_db_path, "health_knowledge.faiss")
            faiss_pkl_path = os.path.join(self.settings.vector_db_path, "health_knowledge.pkl")
            
            if os.path.exists(faiss_index_path) and os.path.exists(faiss_pkl_path):
                # Load existing FAISS index
                self.vector_store = FAISS.load_local(
                    folder_path=self.settings.vector_db_path,
                    embeddings=self.embeddings,
                    index_name="health_knowledge"
                )
                self.logger.info(f"Loaded existing FAISS index from {self.settings.vector_db_path}")
            else:
                # Create new FAISS index
                self.vector_store = None
                self.logger.info("No existing FAISS index found - will create new one when documents are added")

        except Exception as e:
            self.logger.error(f"Failed to initialize vector store: {e}")
            self.vector_store = None

    def _get_sample_knowledge_documents(self) -> List[Document]:
        """
        Get sample health knowledge documents for demonstration.
        In production, these would be loaded from a database or file.
        """
        sample_docs = [
            Document(
                page_content="Regular aerobic exercise strengthens the heart muscle, improves blood circulation, and can help lower blood pressure. The American Heart Association recommends at least 150 minutes of moderate-intensity aerobic activity per week.",
                metadata={"source": "AHA Guidelines", "topic": "exercise", "type": "guideline"}
            ),
            Document(
                page_content="Heart Rate Variability (HRV) measures the variation in time between consecutive heartbeats. Higher HRV generally indicates better cardiovascular health and stress resilience. Low HRV can be associated with stress, poor sleep, or underlying health conditions.",
                metadata={"source": "Cardiology Research", "topic": "hrv", "type": "explanation"}
            ),
            Document(
                page_content="Blood pressure readings consist of two numbers: systolic (top) and diastolic (bottom). Normal blood pressure is below 120/80 mmHg. Hypertension is diagnosed when readings are consistently 130/80 mmHg or higher.",
                metadata={"source": "Medical Guidelines", "topic": "blood_pressure", "type": "definition"}
            ),
            Document(
                page_content="Sleep quality significantly impacts heart health. Adults should aim for 7-9 hours of quality sleep per night. Poor sleep can contribute to high blood pressure, irregular heart rhythms, and increased risk of cardiovascular disease.",
                metadata={"source": "Sleep Medicine", "topic": "sleep", "type": "health_impact"}
            ),
            Document(
                page_content="Stress management is crucial for heart health. Chronic stress can lead to elevated blood pressure, increased heart rate, and inflammation. Techniques like meditation, deep breathing, and regular exercise can help manage stress levels.",
                metadata={"source": "Stress Management", "topic": "stress", "type": "management"}
            ),
            Document(
                page_content="A heart-healthy diet includes plenty of fruits, vegetables, whole grains, lean proteins, and healthy fats. Limit sodium, saturated fats, and added sugars. The Mediterranean diet is particularly beneficial for cardiovascular health.",
                metadata={"source": "Nutrition Guidelines", "topic": "diet", "type": "recommendation"}
            )
        ]
        return sample_docs

    def _populate_vector_store(self):
        """Populate the FAISS vector store with sample documents if empty."""
        if self.vector_store is not None:
            # Vector store already exists and has documents
            return

        try:
            # Create vector store directory if it doesn't exist
            os.makedirs(self.settings.vector_db_path, exist_ok=True)
            
            # Get sample documents
            sample_docs = self._get_sample_knowledge_documents()
            
            # Create new FAISS vector store
            self.vector_store = FAISS.from_documents(
                documents=sample_docs,
                embedding=self.embeddings
            )
            
            # Save the vector store locally
            self.vector_store.save_local(
                folder_path=self.settings.vector_db_path,
                index_name="health_knowledge"
            )
            
            self.logger.info(f"Created and saved FAISS index with {len(sample_docs)} documents to {self.settings.vector_db_path}")

        except Exception as e:
            self.logger.error(f"Failed to populate vector store: {e}")
            self.vector_store = None

    def _retrieve_relevant_documents(self, query: str, k: int = 3) -> List[Document]:
        """
        Retrieve relevant documents from the FAISS vector store.
        
        Args:
            query: The user's query
            k: Number of documents to retrieve
            
        Returns:
            List of relevant documents
        """
        if not self.vector_store:
            self.logger.warning("Vector store not available - returning empty results")
            return []

        try:
            # Search for similar documents
            docs = self.vector_store.similarity_search(query, k=k)
            self.logger.info(f"Retrieved {len(docs)} relevant documents")
            return docs

        except Exception as e:
            self.logger.error(f"Error retrieving documents: {e}")
            return []

    def _format_retrieved_context(self, documents: List[Document]) -> str:
        """
        Format retrieved documents into a context string.
        
        Args:
            documents: List of retrieved documents
            
        Returns:
            Formatted context string
        """
        if not documents:
            return ""

        context_parts = ["Relevant Health Information:"]
        
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get("source", "Unknown")
            topic = doc.metadata.get("topic", "General")
            context_parts.append(f"\n{i}. {doc.page_content}")
            context_parts.append(f"   Source: {source} | Topic: {topic}")

        return "\n".join(context_parts)

    def process(self, state: HealthAssistantState) -> HealthAssistantState:
        """
        Process the state by retrieving relevant knowledge and enriching the context.
        
        Args:
            state: Current conversation state
            
        Returns:
            Updated state with enriched context
        """
        try:
            self.logger.info("Starting RAG retrieval process")

            # Get the latest user message
            if not state.messages:
                self.logger.warning("No messages in state")
                return state

            latest_message = state.messages[-1]
            user_query = latest_message.content

            # Ensure vector store is populated
            self._populate_vector_store()

            # Retrieve relevant documents
            relevant_docs = self._retrieve_relevant_documents(user_query)

            # Format the retrieved context
            rag_context = self._format_retrieved_context(relevant_docs)

            # Add RAG context to the state
            if rag_context:
                # Create a system message with the RAG context
                rag_message = Message(
                    role="system",
                    content=f"Knowledge Context:\n{rag_context}",
                    timestamp=datetime.now().isoformat()
                )
                
                # Add the RAG context message to the conversation
                state.messages.append(rag_message)
                
                self.logger.info(f"Added RAG context with {len(relevant_docs)} documents")
            else:
                self.logger.info("No relevant documents found")

            # Update state to indicate RAG processing was completed
            state.current_intent = state.current_intent or "KNOWLEDGE_QUERY"
            
            return state

        except Exception as e:
            self.logger.error(f"Error in RAG processing: {e}")
            return state

    def get_system_prompt(self) -> str:
        """Return the system prompt for this RAG agent."""
        return """You are a Health Knowledge Retrieval Agent.

Your role is to:
1. Retrieve relevant health knowledge documents from the vector store
2. Enhance conversation context with authoritative health information
3. Provide evidence-based insights and recommendations
4. Ensure information is current and medically accurate

Knowledge areas available:
- Exercise and cardiovascular health guidelines
- Heart rate variability and stress management
- Blood pressure monitoring and interpretation
- Sleep quality and heart health relationships
- Stress management techniques
- Heart-healthy nutrition recommendations

Always:
- Cite sources when providing information
- Distinguish between general advice and medical recommendations
- Flag when professional medical consultation is needed
- Provide actionable, personalized insights"""

    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about this agent."""
        return {
            "agent_type": "FAISSRAGAgent",
            "capabilities": [
                "Document retrieval from FAISS vector store",
                "Semantic search using local sentence-transformers",
                "Context enrichment for knowledge queries",
                "Local vector storage (no external dependencies)"
            ],
            "vector_store_available": self.vector_store is not None,
            "embeddings_available": self.embeddings is not None,
            "vector_db_path": self.settings.vector_db_path
        } 