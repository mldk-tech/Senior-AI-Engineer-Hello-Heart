"""
Chat router for Hello Heart AI Assistant API.

This module provides endpoints for conversational AI interactions,
including message processing, conversation management, and context handling.
"""

import time
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
import structlog

from app.api.schemas import (
    ChatRequest, ChatResponse, ConversationHistory, ChatMessage,
    MessageRole, IntentType, SafetyLevel
)
from app.api.dependencies import (
    get_current_user, get_optional_user, get_assistant,
    rate_limit, get_metrics_collector, in_memory_storage,
    get_conversation_context, save_conversation_context
)
from app.core.monitoring import get_metrics_collector
from app.core.security import sanitize_input

# Structured logging
logger = structlog.get_logger()

# Create router
router = APIRouter()


@router.post("/send", response_model=ChatResponse)
@rate_limit(requests_per_minute=30, requests_per_hour=500)
async def send_message(
    request: ChatRequest,
    current_user = Depends(get_optional_user),
    assistant = Depends(get_assistant)
):
    """Send a message to the AI assistant."""
    start_time = time.time()
    
    try:
        # Sanitize input
        sanitized_message = sanitize_input(request.message)
        
        # Get or create conversation ID
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Get conversation context
        context = await get_conversation_context(conversation_id, request.user_id)
        
        # Add user message to context
        user_message = ChatMessage(
            role=MessageRole.USER,
            content=sanitized_message,
            timestamp=datetime.now()
        )
        context["messages"].append(user_message.dict())
        
        # Process message through assistant
        logger.info(
            "Processing chat message",
            user_id=request.user_id,
            conversation_id=conversation_id,
            message_length=len(sanitized_message)
        )
        
        response_text = assistant.process_message(sanitized_message)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Create assistant message
        assistant_message = ChatMessage(
            role=MessageRole.ASSISTANT,
            content=response_text,
            timestamp=datetime.now()
        )
        context["messages"].append(assistant_message.dict())
        
        # Save updated context
        await save_conversation_context(conversation_id, request.user_id, context)
        
        # Record metrics
        metrics_collector = get_metrics_collector()
        if current_user:
            metrics_collector.record_user_interaction(
                current_user.user_id,
                "chat_message"
            )
        
        # Determine intent and safety level (simplified)
        intent = IntentType.HEALTH_QUERY  # This would come from assistant
        safety_level = SafetyLevel.SAFE   # This would come from assistant
        
        # Create response
        response = ChatResponse(
            success=True,
            message="Message processed successfully",
            response=response_text,
            conversation_id=conversation_id,
            intent=intent,
            safety_level=safety_level,
            requires_medical_disclaimer=False,
            follow_up_suggestions=[
                "Would you like to know more about your health data?",
                "I can help you track your activity goals.",
                "Let me know if you have any questions about your blood pressure."
            ],
            confidence_score=0.85,
            health_insights={
                "summary": "Your health data looks good overall",
                "trends": "Improving trends in activity and sleep",
                "recommendations": ["Continue your current exercise routine", "Maintain good sleep hygiene"]
            }
        )
        
        # Record assistant metrics
        metrics_collector.record_assistant_request(
            intent=intent.value,
            safety_level=safety_level.value,
            response_time=processing_time,
            confidence=response.confidence_score
        )
        
        logger.info(
            "Chat message processed successfully",
            user_id=request.user_id,
            conversation_id=conversation_id,
            processing_time=processing_time,
            intent=intent.value,
            safety_level=safety_level.value
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "Error processing chat message",
            user_id=request.user_id,
            error=str(e)
        )
        
        # Record error metrics
        metrics_collector = get_metrics_collector()
        metrics_collector.record_error("chat_message_processing", str(e))
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message"
        )


@router.get("/conversations/{conversation_id}", response_model=ConversationHistory)
async def get_conversation_history(
    conversation_id: str,
    user_id: str,
    current_user = Depends(get_current_user)
):
    """Get conversation history for a specific conversation."""
    try:
        # Validate access
        if current_user.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to conversation"
            )
        
        # Get conversation context
        context = await get_conversation_context(conversation_id, user_id)
        
        # Convert to response format
        messages = []
        for msg_data in context.get("messages", []):
            message = ChatMessage(
                role=MessageRole(msg_data["role"]),
                content=msg_data["content"],
                timestamp=datetime.fromisoformat(msg_data["timestamp"])
            )
            messages.append(message)
        
        return ConversationHistory(
            conversation_id=conversation_id,
            user_id=user_id,
            messages=messages,
            metadata=context.get("metadata", {}),
            created_at=context.get("metadata", {}).get("created_at"),
            last_updated=context.get("metadata", {}).get("last_updated")
        )
        
    except Exception as e:
        logger.error(
            "Error retrieving conversation history",
            conversation_id=conversation_id,
            user_id=user_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation history"
        )


@router.get("/conversations", response_model=list[ConversationHistory])
async def list_conversations(
    user_id: str,
    limit: int = 10,
    offset: int = 0,
    current_user = Depends(get_current_user)
):
    """List all conversations for a user."""
    try:
        # Validate access
        if current_user.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to conversations"
            )
        
        # Get all conversations for user (simplified for POC)
        conversations = []
        # In a real implementation, you would query the storage
        # For POC, we'll return an empty list or mock data
        
        return conversations
        
    except Exception as e:
        logger.error(
            "Error listing conversations",
            user_id=user_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list conversations"
        )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user_id: str,
    current_user = Depends(get_current_user)
):
    """Delete a conversation."""
    try:
        # Validate access
        if current_user.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to conversation"
            )
        
        # Delete conversation from in-memory storage
        key = f"{user_id}:{conversation_id}"
        if key in in_memory_storage["conversations"]:
            del in_memory_storage["conversations"][key]
        
        logger.info(
            "Conversation deleted",
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        return {"message": "Conversation deleted successfully"}
        
    except Exception as e:
        logger.error(
            "Error deleting conversation",
            conversation_id=conversation_id,
            user_id=user_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation"
        )


@router.post("/conversations/{conversation_id}/clear")
async def clear_conversation(
    conversation_id: str,
    user_id: str,
    current_user = Depends(get_current_user)
):
    """Clear all messages from a conversation."""
    try:
        # Validate access
        if current_user.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to conversation"
            )
        
        # Clear conversation messages
        key = f"{user_id}:{conversation_id}"
        if key in in_memory_storage["conversations"]:
            in_memory_storage["conversations"][key]["messages"] = []
            in_memory_storage["conversations"][key]["metadata"]["last_updated"] = datetime.now().isoformat()
        
        logger.info(
            "Conversation cleared",
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        return {"message": "Conversation cleared successfully"}
        
    except Exception as e:
        logger.error(
            "Error clearing conversation",
            conversation_id=conversation_id,
            user_id=user_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear conversation"
        )


@router.post("/stream")
async def stream_chat(
    request: ChatRequest,
    current_user = Depends(get_optional_user),
    assistant = Depends(get_assistant)
):
    """Stream chat response (for real-time interactions)."""
    # This would implement Server-Sent Events (SSE) for streaming
    # For now, we'll return a simple response
    try:
        sanitized_message = sanitize_input(request.message)
        response_text = assistant.process_message(sanitized_message)
        
        return {
            "success": True,
            "message": "Stream response",
            "data": {
                "response": response_text,
                "streaming": True
            }
        }
        
    except Exception as e:
        logger.error("Error in stream chat", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stream response"
        )


@router.get("/suggestions")
async def get_chat_suggestions(
    user_id: str,
    context: Optional[str] = None,
    current_user = Depends(get_optional_user)
):
    """Get chat suggestions based on context."""
    try:
        # Generate contextual suggestions
        suggestions = [
            "How did I sleep last night?",
            "Am I meeting my activity goals?",
            "What's my blood pressure trend?",
            "Can you explain heart rate variability?",
            "I'm feeling stressed, any breathing exercises?"
        ]
        
        # Filter based on context if provided
        if context:
            if "sleep" in context.lower():
                suggestions = [s for s in suggestions if "sleep" in s.lower()]
            elif "activity" in context.lower():
                suggestions = [s for s in suggestions if "activity" in s.lower()]
            elif "blood" in context.lower():
                suggestions = [s for s in suggestions if "blood" in s.lower()]
        
        return {
            "success": True,
            "message": "Suggestions retrieved successfully",
            "suggestions": suggestions[:5]  # Limit to 5 suggestions
        }
        
    except Exception as e:
        logger.error("Error getting chat suggestions", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get suggestions"
        )


@router.post("/feedback")
async def submit_chat_feedback(
    conversation_id: str,
    user_id: str,
    message_id: str,
    rating: int,  # 1-5 scale
    feedback: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """Submit feedback for a chat message."""
    try:
        # Validate access
        if current_user.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to conversation"
            )
        
        # Validate rating
        if not 1 <= rating <= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rating must be between 1 and 5"
            )
        
        # Store feedback in memory (in a real app, this would go to a database)
        feedback_key = f"feedback:{conversation_id}:{message_id}"
        feedback_data = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "message_id": message_id,
            "rating": rating,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in memory (simplified for POC)
        if "feedback" not in in_memory_storage:
            in_memory_storage["feedback"] = {}
        in_memory_storage["feedback"][feedback_key] = feedback_data
        
        # Record metrics
        metrics_collector = get_metrics_collector()
        metrics_collector.record_user_feedback(rating, feedback is not None)
        
        logger.info(
            "Chat feedback submitted",
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            rating=rating
        )
        
        return {"message": "Feedback submitted successfully"}
        
    except Exception as e:
        logger.error(
            "Error submitting feedback",
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback"
        ) 