#!/usr/bin/env python3
"""
Test script for local sentence-transformers embeddings and FAISS vector store.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.agents.rag import LocalEmbeddings, FAISSRAGAgent
from app.core.config import get_settings

def test_local_embeddings():
    """Test local embeddings functionality."""
    print("🧪 Testing Local Embeddings...")
    
    try:
        # Initialize local embeddings
        settings = get_settings()
        embeddings = LocalEmbeddings(model_name=settings.embedding_model)
        
        # Test documents
        test_docs = [
            "Heart Rate Variability (HRV) measures the variation in time between consecutive heartbeats.",
            "Blood pressure readings consist of two numbers: systolic and diastolic.",
            "Regular aerobic exercise strengthens the heart muscle and improves blood circulation."
        ]
        
        # Test query
        test_query = "What is heart rate variability?"
        
        print(f"✅ Using model: {settings.embedding_model}")
        
        # Test document embeddings
        doc_embeddings = embeddings.embed_documents(test_docs)
        print(f"✅ Document embeddings shape: {len(doc_embeddings)} x {len(doc_embeddings[0])}")
        
        # Test query embedding
        query_embedding = embeddings.embed_query(test_query)
        print(f"✅ Query embedding shape: {len(query_embedding)}")
        
        # Test similarity (simple cosine similarity)
        import numpy as np
        
        def cosine_similarity(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        
        similarities = []
        for i, doc_emb in enumerate(doc_embeddings):
            sim = cosine_similarity(query_embedding, doc_emb)
            similarities.append((i, sim))
            print(f"   Document {i+1} similarity: {sim:.4f}")
        
        # Find most similar document
        best_match = max(similarities, key=lambda x: x[1])
        print(f"✅ Best match: Document {best_match[0]+1} (similarity: {best_match[1]:.4f})")
        
        print("🎉 Local embeddings test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing local embeddings: {e}")
        return False

def test_faiss_rag():
    """Test FAISS RAG functionality."""
    print("\n🔍 Testing FAISS RAG Agent...")
    
    try:
        # Initialize FAISS RAG agent
        rag_agent = FAISSRAGAgent()
        
        print(f"✅ FAISS RAG Agent initialized")
        print(f"✅ Vector store available: {rag_agent.vector_store is not None}")
        print(f"✅ Embeddings available: {rag_agent.embeddings is not None}")
        print(f"✅ Vector DB path: {rag_agent.settings.vector_db_path}")
        
        # Test document retrieval
        test_query = "What is heart rate variability?"
        relevant_docs = rag_agent._retrieve_relevant_documents(test_query, k=2)
        
        print(f"✅ Retrieved {len(relevant_docs)} relevant documents")
        
        for i, doc in enumerate(relevant_docs):
            print(f"   Document {i+1}: {doc.page_content[:100]}...")
            print(f"   Source: {doc.metadata.get('source', 'Unknown')}")
        
        print("🎉 FAISS RAG test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing FAISS RAG: {e}")
        return False

if __name__ == "__main__":
    success1 = test_local_embeddings()
    success2 = test_faiss_rag()
    
    if success1 and success2:
        print("\n🎉 All tests passed! FAISS RAG is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        sys.exit(1) 