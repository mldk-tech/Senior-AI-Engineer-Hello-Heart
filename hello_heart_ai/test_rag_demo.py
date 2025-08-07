#!/usr/bin/env python3
"""
Demo script to test RAG (Retrieval-Augmented Generation) integration.

This script tests the Redis RAG agent with various knowledge queries
to demonstrate how the system retrieves relevant health information.
"""

import sys
import os
import logging
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import setup_logging, get_system_info
from app.orchestration.workflow import HealthAIAssistant


def test_rag_integration():
    """Test the RAG integration with various knowledge queries."""
    
    # Set up logging
    setup_logging()
    logger = logging.getLogger("rag_demo")
    
    print("=" * 60)
    print("RAG Integration Demo - Hello Heart AI Assistant")
    print("=" * 60)
    
    # Get system info
    system_info = get_system_info()
    print(f"System Status: {system_info['status']}")
    print(f"LangGraph Available: {system_info['langgraph_available']}")
    print(f"LLM Configured: {system_info['llm_configured']}")
    print()
    
    # Initialize the assistant
    try:
        assistant = HealthAIAssistant()
        print("✅ Assistant initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize assistant: {e}")
        return
    
    # Test knowledge queries
    knowledge_queries = [
        "What are the benefits of aerobic exercise for heart health?",
        "Can you explain what Heart Rate Variability (HRV) means?",
        "What is considered normal blood pressure?",
        "How does sleep quality affect heart health?",
        "What are some stress management techniques for heart health?",
        "What should I eat for a heart-healthy diet?"
    ]
    
    print("\n" + "=" * 60)
    print("Testing Knowledge Queries with RAG")
    print("=" * 60)
    
    for i, query in enumerate(knowledge_queries, 1):
        print(f"\n--- Test {i}: {query} ---")
        
        try:
            # Process the query
            response = assistant.process_message(query)
            
            print(f"Response: {response}")
            
            # Get system status to check agent info
            status = assistant.get_system_status()
            rag_info = status.get("agents", {}).get("rag", {})
            
            if rag_info:
                print(f"RAG Agent Status: {rag_info.get('vector_store_available', False)}")
                print(f"Embeddings Available: {rag_info.get('embeddings_available', False)}")
            
        except Exception as e:
            print(f"❌ Error processing query: {e}")
        
        print("-" * 40)
    
    # Test mixed queries to show routing
    print("\n" + "=" * 60)
    print("Testing Mixed Queries (Knowledge vs Personal Data)")
    print("=" * 60)
    
    mixed_queries = [
        ("Knowledge Query", "What is the importance of regular exercise?"),
        ("Personal Data Query", "How many steps did I take today?"),
        ("Knowledge Query", "Explain the relationship between stress and heart health"),
        ("Personal Data Query", "What was my blood pressure reading yesterday?")
    ]
    
    for query_type, query in mixed_queries:
        print(f"\n--- {query_type}: {query} ---")
        
        try:
            response = assistant.process_message(query)
            print(f"Response: {response}")
            
        except Exception as e:
            print(f"❌ Error processing query: {e}")
        
        print("-" * 40)
    
    print("\n" + "=" * 60)
    print("RAG Demo Completed")
    print("=" * 60)


if __name__ == "__main__":
    test_rag_integration() 