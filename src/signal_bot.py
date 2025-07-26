"""
Signal bot for Note to Self integration
Replaces telegram_bot.py with Signal-based communication
"""

import asyncio
import logging
import structlog
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .models import Meeting, Conversation
from .config import settings
from .services.signal_service import SignalService
from .services.meeting_processor import MeetingProcessor
from .ollama_client import OllamaClient
from .vector_store import VectorStore
from .config import settings

logger = structlog.get_logger()


class SignalBot:
    """Signal bot for Note to Self communication"""
    
    def __init__(self, vector_store: VectorStore, ollama_client: OllamaClient):
        self.signal_service = SignalService()
        self.vector_store = vector_store
        self.ollama_client = ollama_client
        self.meeting_processor = MeetingProcessor(vector_store, ollama_client)
        self.is_running = False
        self.last_processed_timestamp = 0
        
    async def initialize(self):
        """Initialize the Signal bot"""
        try:
            # Check if Signal CLI is configured
            if not await self.signal_service.check_signal_cli():
                logger.error("Signal CLI not configured. Please run setup first.")
                return False
            
            # Get account info
            account_info = await self.signal_service.get_account_info()
            if account_info:
                logger.info("Signal bot initialized", account=account_info)
            else:
                logger.error("Failed to get Signal account info")
                return False
            
            # Send startup message
            await self.signal_service.send_message(
                "🤖 Personal AI Assistant is now active!\n\n"
                "Send me meeting notes and I'll:\n"
                "• Extract action items\n"
                "• Create calendar reminders\n"
                "• Summarize key points\n"
                "• Answer questions about your meetings\n\n"
                "Just send your meeting content to this Note to Self chat!"
            )
            
            return True
            
        except Exception as e:
            logger.error("Failed to initialize Signal bot", error=str(e))
            return False
    
    async def start_monitoring(self):
        """Start monitoring Signal messages"""
        if self.is_running:
            logger.warning("Signal bot is already running")
            return
        
        self.is_running = True
        logger.info("Starting Signal message monitoring...")
        
        try:
            await self.signal_service.start_monitoring(self.handle_message)
        except Exception as e:
            logger.error("Error in Signal monitoring", error=str(e))
        finally:
            self.is_running = False
    
    def stop_monitoring(self):
        """Stop monitoring Signal messages"""
        self.is_running = False
        self.signal_service.stop_monitoring()
        logger.info("Stopped Signal message monitoring")
    
    async def handle_message(self, message_text: str, timestamp: int):
        """Handle incoming Signal message"""
        try:
            # Avoid processing old messages or duplicates
            if timestamp <= self.last_processed_timestamp:
                return
            
            self.last_processed_timestamp = timestamp
            
            logger.info("Processing Signal message", 
                       message_length=len(message_text),
                       timestamp=timestamp)
            
            # Process the message
            start_time = datetime.utcnow()
            
            try:
                response = await self.process_user_message(message_text)
                
                # Send response back to Note to Self
                if response:
                    await self.signal_service.send_message(response)
                
                # Calculate processing time
                processing_time = (datetime.utcnow() - start_time).total_seconds()
                
                # Store conversation in database
                async with get_db() as session:
                    conversation = Conversation(
                        chat_id=settings.signal_phone_number,  # Use phone number as chat_id
                        user_message=message_text,
                        bot_response=response,
                        message_type="query" if not self.is_meeting_content(message_text) else "meeting",
                        processing_time=int(processing_time)
                    )
                    session.add(conversation)
                    await session.commit()
                
                logger.info("Message processed successfully", 
                           processing_time=processing_time)
                
            except Exception as e:
                logger.error("Error processing message", error=str(e))
                await self.signal_service.send_message(
                    "Sorry, I encountered an error processing your message. Please try again later."
                )
        
        except Exception as e:
            logger.error("Error handling Signal message", error=str(e))
    
    async def process_user_message(self, message: str) -> str:
        """Process user message and generate response"""
        try:
            # Check if Signal is configured
            if not settings.signal_phone_number:
                return "Signal phone number not configured. Please set SIGNAL_PHONE_NUMBER in environment."
            
            # Check if this looks like meeting content
            if self.is_meeting_content(message):
                return await self.process_meeting_content(message)
            else:
                return await self.process_query(message)
                
        except Exception as e:
            logger.error("Error processing user message", error=str(e))
            return "I'm sorry, I encountered an error processing your message. Please try again."
    
    def is_meeting_content(self, message: str) -> bool:
        """Determine if message contains meeting content"""
        meeting_indicators = [
            "meeting", "discussed", "action items", "follow up", 
            "agenda", "attendees", "participants", "minutes",
            "next steps", "decisions", "twinmind", "transcript",
            "call with", "meeting with", "zoom", "teams"
        ]
        
        message_lower = message.lower()
        indicator_count = sum(1 for indicator in meeting_indicators if indicator in message_lower)
        
        # Consider it meeting content if:
        # - Has meeting indicators AND is reasonably long
        # - OR has multiple meeting indicators
        return (indicator_count >= 1 and len(message) > 100) or indicator_count >= 2
    
    async def process_meeting_content(self, content: str) -> str:
        """Process meeting content and extract action items"""
        try:
            logger.info("Processing meeting content", content_length=len(content))
            
            async with get_db() as session:
                result = await self.meeting_processor.process_meeting(
                    content, 
                    chat_id=settings.signal_phone_number,
                    db=session
                )
            
            # Send calendar files if any were created
            if result.get("calendar_files"):
                calendar_count = await self.signal_service.send_multiple_calendar_files(
                    result["calendar_files"]
                )
                logger.info("Sent calendar files", count=calendar_count)
            
            return result.get("summary", "Meeting processed successfully!")
            
        except Exception as e:
            logger.error("Error processing meeting content", error=str(e))
            return "I processed your meeting content, but encountered some issues. The meeting has been saved for review."
    
    async def process_query(self, query: str) -> str:
        """Process user query with context from previous meetings"""
        try:
            logger.info("Processing query", query=query[:100])
            
            # Get relevant context from vector store
            context = await self.vector_store.get_meeting_context(query)
            
            # Generate response using Ollama with context
            system_prompt = """You are a helpful personal AI assistant. The user is asking a question about their meetings and work.

Use the provided context from their previous meetings to answer their question. 
If the context contains relevant information, use it to provide a specific, helpful answer.
If the context doesn't contain relevant information, say so and offer to help in other ways.

Be conversational but professional. Keep responses concise but complete."""

            prompt = f"""Context from previous meetings:
{context}

Question: {query}"""

            response = await self.ollama_client.generate_response(prompt, system_prompt)
            
            return response
            
        except Exception as e:
            logger.error("Error processing query", error=str(e))
            return "I'm having trouble accessing your meeting history right now. Please try again later."
    
    async def send_proactive_reminder(self, message: str):
        """Send proactive reminder to Note to Self"""
        try:
            await self.signal_service.send_message(f"🔔 Reminder: {message}")
            logger.info("Sent proactive reminder")
        except Exception as e:
            logger.error("Error sending proactive reminder", error=str(e))
    
    async def health_check(self) -> bool:
        """Check if Signal bot is healthy"""
        try:
            return await self.signal_service.check_signal_cli()
        except Exception as e:
            logger.error("Signal bot health check failed", error=str(e))
            return False
    
    async def get_status(self) -> Dict[str, Any]:
        """Get Signal bot status"""
        try:
            account_info = await self.signal_service.get_account_info()
            return {
                "status": "running" if self.is_running else "stopped",
                "account": account_info,
                "last_processed": self.last_processed_timestamp
            }
        except Exception as e:
            logger.error("Error getting Signal bot status", error=str(e))
            return {"status": "error", "error": str(e)}
    
    async def stop(self):
        """Stop the Signal bot"""
        self.stop_monitoring()
        await self.signal_service.cleanup()
        logger.info("Signal bot stopped")


# Global instance for use in main.py
signal_bot: Optional[SignalBot] = None


async def get_signal_bot() -> Optional[SignalBot]:
    """Get the global Signal bot instance"""
    return signal_bot


async def initialize_signal_bot(vector_store: VectorStore, ollama_client: OllamaClient) -> SignalBot:
    """Initialize the global Signal bot instance"""
    global signal_bot
    signal_bot = SignalBot(vector_store, ollama_client)
    await signal_bot.initialize()
    return signal_bot