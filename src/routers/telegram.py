"""
Telegram bot integration
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.orm import Session
import logging
from datetime import datetime
from typing import Dict, Any

from ..database import get_db, Conversation
from ..config import settings
from ..services.telegram_service import TelegramService
from ..services.ollama_service import OllamaService

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
telegram_service = TelegramService()
ollama_service = OllamaService()


@router.post("/webhook")
async def telegram_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Telegram webhook updates"""
    try:
        # Get the update data
        update_data = await request.json()
        logger.info(f"Received Telegram update: {update_data}")
        
        # Extract message info
        if "message" not in update_data:
            return {"status": "ok"}  # Not a message update
        
        message = update_data["message"]
        chat_id = str(message["chat"]["id"])
        user_message = message.get("text", "")
        
        if not user_message:
            # Handle non-text messages (files, etc.)
            await telegram_service.send_message(
                chat_id, 
                "I can only process text messages right now. Please send me meeting notes or ask questions about your meetings!"
            )
            return {"status": "ok"}
        
        # Process the message
        start_time = datetime.utcnow()
        
        try:
            # Generate response using Ollama
            bot_response = await process_user_message(user_message, chat_id, db)
            
            # Send response back to user
            await telegram_service.send_message(chat_id, bot_response)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Store conversation in database
            conversation = Conversation(
                chat_id=chat_id,
                user_message=user_message,
                bot_response=bot_response,
                message_type="query",
                processing_time=processing_time
            )
            db.add(conversation)
            db.commit()
            
            logger.info(f"Processed message in {processing_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await telegram_service.send_message(
                chat_id,
                "Sorry, I encountered an error processing your message. Please try again later."
            )
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def process_user_message(message: str, chat_id: str, db: Session) -> str:
    """Process user message and generate response"""
    try:
        # Check if this looks like meeting content
        if is_meeting_content(message):
            return await process_meeting_content(message, chat_id, db)
        else:
            return await process_query(message, chat_id, db)
            
    except Exception as e:
        logger.error(f"Error processing user message: {e}")
        return "I'm sorry, I encountered an error processing your message. Please try again."


def is_meeting_content(message: str) -> bool:
    """Determine if message contains meeting content"""
    meeting_indicators = [
        "meeting", "discussed", "action items", "follow up", 
        "agenda", "attendees", "participants", "minutes",
        "next steps", "decisions", "twinmind"
    ]
    
    message_lower = message.lower()
    return any(indicator in message_lower for indicator in meeting_indicators) and len(message) > 100


async def process_meeting_content(content: str, chat_id: str, db: Session) -> str:
    """Process meeting content and extract action items"""
    try:
        # This will be implemented in meeting_processor.py
        from ..services.meeting_processor import MeetingProcessor
        
        processor = MeetingProcessor()
        result = await processor.process_meeting(content, chat_id, db)
        
        return result["summary"]
        
    except Exception as e:
        logger.error(f"Error processing meeting content: {e}")
        return "I processed your meeting content, but encountered some issues. The meeting has been saved for review."


async def process_query(query: str, chat_id: str, db: Session) -> str:
    """Process user query with context from previous meetings"""
    try:
        # Get relevant context from vector store
        from ..vector_store import VectorStore
        
        vector_store = VectorStore()
        await vector_store.initialize()
        
        context = await vector_store.get_meeting_context(query)
        
        # Generate response using Ollama with context
        prompt = f"""You are a helpful personal AI assistant. The user is asking: "{query}"

Here is relevant context from their previous meetings:
{context}

Please provide a helpful, concise response based on the context. If no relevant context is available, let them know and offer to help in other ways."""

        response = await ollama_service.generate_response(prompt)
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return "I'm having trouble accessing your meeting history right now. Please try again later."


@router.get("/set-webhook")
async def set_webhook():
    """Set up Telegram webhook (for development/testing)"""
    try:
        if not settings.telegram_webhook_url:
            raise HTTPException(status_code=400, detail="Webhook URL not configured")
        
        success = await telegram_service.set_webhook(settings.telegram_webhook_url + "/telegram/webhook")
        
        if success:
            return {"status": "webhook set successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to set webhook")
            
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))