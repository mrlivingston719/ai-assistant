"""
Telegram Bot Implementation for RovoDev
Handles both webhook and polling modes with meeting processing
"""

import asyncio
import structlog
from typing import Optional, Dict, Any
from datetime import datetime
import json

from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from telegram.error import TelegramError

from .config import settings
from .database import get_db
from .models import User, Meeting, ActionItem, Conversation
from .services.meeting_processor import MeetingProcessor
from .services.calendar_service import CalendarService

logger = structlog.get_logger()


class TelegramBot:
    """Main Telegram bot class"""
    
    def __init__(self, vector_store, ollama_client):
        self.vector_store = vector_store
        self.ollama_client = ollama_client
        self.application = None
        self.meeting_processor = None
        self.calendar_service = None
        self.bot = None
        
    async def initialize(self):
        """Initialize the Telegram bot"""
        try:
            # Create bot application
            self.application = Application.builder().token(settings.telegram_bot_token).build()
            self.bot = self.application.bot
            
            # Initialize services
            self.meeting_processor = MeetingProcessor(self.vector_store, self.ollama_client)
            self.calendar_service = CalendarService()
            
            # Add handlers
            self._add_handlers()
            
            # Initialize the application
            await self.application.initialize()
            
            logger.info("Telegram bot initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Telegram bot", error=str(e))
            raise
    
    def _add_handlers(self):
        """Add message and command handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        
        # Message handlers
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
        
    async def start_polling(self):
        """Start polling for updates"""
        try:
            await self.application.start()
            await self.application.updater.start_polling()
            logger.info("Telegram bot polling started")
        except Exception as e:
            logger.error("Failed to start polling", error=str(e))
            raise
    
    async def stop(self):
        """Stop the bot"""
        try:
            if self.application:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
            logger.info("Telegram bot stopped")
        except Exception as e:
            logger.error("Error stopping bot", error=str(e))
    
    async def handle_webhook(self, update_data: dict):
        """Handle webhook updates"""
        try:
            update = Update.de_json(update_data, self.bot)
            await self.application.process_update(update)
        except Exception as e:
            logger.error("Error processing webhook update", error=str(e))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # Create or update user in database
        async with get_db() as db:
            db_user = await self._get_or_create_user(db, user)
            
        welcome_message = f"""
🤖 **Welcome to RovoDev - Your Personal AI Assistant!**

Hi {user.first_name}! I'm here to help you process meetings and manage your tasks.

**What I can do:**
📝 Process meeting transcripts and extract action items
📅 Create iOS calendar reminders
🔍 Answer questions about your meetings
📊 Summarize and categorize your meetings

**How to use me:**
1. Send me meeting notes or transcripts
2. Ask questions about your previous meetings
3. I'll automatically extract action items and create calendar reminders

**Commands:**
/help - Show this help message
/status - Check system status

Just send me a meeting transcript to get started! 🚀
"""
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        logger.info(f"New user started bot: {user.id}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = """
🆘 **RovoDev Help**

**Meeting Processing:**
• Send meeting transcripts (any length)
• I'll extract action items automatically
• Get iOS calendar files for reminders

**Questions & Queries:**
• Ask about previous meetings
• Search your meeting history
• Get summaries and insights

**Examples:**
• "What were the action items from yesterday's meeting?"
• "When is my next deadline?"
• "Summarize all meetings about project X"

**Tips:**
• Include participant names for better processing
• Mention dates and deadlines clearly
• Use keywords like "action item" or "follow up"

Need more help? Contact support or check the documentation.
"""
        
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        try:
            # Check system health
            status_message = "🔍 **System Status**\n\n"
            
            # Check Ollama
            try:
                await self.ollama_client.health_check()
                status_message += "✅ AI Model: Online\n"
            except:
                status_message += "❌ AI Model: Offline\n"
            
            # Check Vector Store
            try:
                await self.vector_store.health_check()
                status_message += "✅ Vector Database: Online\n"
            except:
                status_message += "❌ Vector Database: Offline\n"
            
            # Get user stats
            async with get_db() as db:
                user = await self._get_or_create_user(db, update.effective_user)
                meeting_count = await db.execute(
                    "SELECT COUNT(*) FROM meetings WHERE user_id = ?", (user.id,)
                ).scalar()
                action_count = await db.execute(
                    "SELECT COUNT(*) FROM action_items WHERE user_id = ? AND status = 'pending'", (user.id,)
                ).scalar()
            
            status_message += f"\n📊 **Your Stats:**\n"
            status_message += f"• Meetings processed: {meeting_count or 0}\n"
            status_message += f"• Pending action items: {action_count or 0}\n"
            
            await update.message.reply_text(status_message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error("Error in status command", error=str(e))
            await update.message.reply_text("❌ Unable to get system status")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        try:
            user = update.effective_user
            message_text = update.message.text
            chat_id = update.effective_chat.id
            
            # Get or create user
            async with get_db() as db:
                db_user = await self._get_or_create_user(db, user)
                
                # Determine if this is meeting content or a query
                if self._is_meeting_content(message_text):
                    await self._process_meeting_content(update, db_user, message_text)
                else:
                    await self._process_query(update, db_user, message_text)
                    
        except Exception as e:
            logger.error("Error handling message", error=str(e))
            await update.message.reply_text(
                "❌ Sorry, I encountered an error processing your message. Please try again."
            )
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document uploads"""
        try:
            document = update.message.document
            
            # Check if it's a text file
            if document.mime_type and 'text' in document.mime_type:
                # Download and process the file
                file = await context.bot.get_file(document.file_id)
                file_content = await file.download_as_bytearray()
                text_content = file_content.decode('utf-8')
                
                # Process as meeting content
                user = update.effective_user
                async with get_db() as db:
                    db_user = await self._get_or_create_user(db, user)
                    await self._process_meeting_content(update, db_user, text_content)
            else:
                await update.message.reply_text(
                    "📄 I can only process text files. Please send meeting notes as text or a .txt file."
                )
                
        except Exception as e:
            logger.error("Error handling document", error=str(e))
            await update.message.reply_text(
                "❌ Error processing document. Please try sending the content as text."
            )
    
    def _is_meeting_content(self, text: str) -> bool:
        """Determine if text contains meeting content"""
        meeting_indicators = [
            'meeting', 'discussed', 'action items', 'follow up', 'agenda',
            'attendees', 'participants', 'minutes', 'next steps', 'decisions',
            'twinmind', 'transcript', 'recording'
        ]
        
        text_lower = text.lower()
        indicator_count = sum(1 for indicator in meeting_indicators if indicator in text_lower)
        
        # Consider it meeting content if it has multiple indicators and is substantial
        return indicator_count >= 2 and len(text) > 100
    
    async def _process_meeting_content(self, update: Update, user: User, content: str):
        """Process meeting content and extract action items"""
        try:
            # Send processing message
            processing_msg = await update.message.reply_text(
                "🔄 Processing your meeting... This may take a moment."
            )
            
            # Process the meeting
            result = await self.meeting_processor.process_meeting(content, user.id)
            
            # Delete processing message
            await processing_msg.delete()
            
            # Send summary
            summary_text = f"✅ **Meeting Processed Successfully**\n\n"
            summary_text += f"📝 **Summary:**\n{result['summary']}\n\n"
            summary_text += f"📊 **Category:** {result['category']}\n"
            summary_text += f"🎯 **Action Items:** {len(result['action_items'])}"
            
            await update.message.reply_text(summary_text, parse_mode='Markdown')
            
            # Send calendar files if action items exist
            if result['action_items']:
                calendar_files = []
                for action_item in result['action_items']:
                    if action_item.get('due_date'):
                        ics_content = await self.calendar_service.create_reminder(
                            title=action_item['title'],
                            description=action_item.get('description', ''),
                            due_date=action_item['due_date'],
                            reminder_minutes=user.default_reminder_minutes
                        )
                        calendar_files.append({
                            'content': ics_content,
                            'filename': f"{action_item['title'][:30]}.ics"
                        })
                
                # Send calendar files
                if calendar_files:
                    await update.message.reply_text(
                        f"📅 Created {len(calendar_files)} calendar reminder(s):"
                    )
                    
                    for cal_file in calendar_files:
                        await update.message.reply_document(
                            document=cal_file['content'].encode('utf-8'),
                            filename=cal_file['filename'],
                            caption="📱 Tap to add to iOS Calendar"
                        )
            
        except Exception as e:
            logger.error("Error processing meeting content", error=str(e))
            await update.message.reply_text(
                "❌ Error processing meeting. The content has been saved but may need manual review."
            )
    
    async def _process_query(self, update: Update, user: User, query: str):
        """Process user query with context"""
        try:
            # Send typing indicator
            await update.message.reply_chat_action('typing')
            
            # Get relevant context from vector store
            context = await self.vector_store.search_meetings(query, user_id=user.id, limit=3)
            
            # Generate response using Ollama
            system_prompt = """You are a helpful personal AI assistant. Use the provided context from the user's meetings to answer their question accurately and helpfully. If the context doesn't contain relevant information, say so and offer to help in other ways."""
            
            context_text = "\n".join([f"Meeting: {item['content']}" for item in context])
            prompt = f"Context:\n{context_text}\n\nQuestion: {query}"
            
            response = await self.ollama_client.generate_response(prompt, system_prompt)
            
            await update.message.reply_text(response)
            
            # Store conversation
            async with get_db() as db:
                conversation = Conversation(
                    user_id=user.id,
                    message_type='query',
                    content=f"Q: {query}\nA: {response}"
                )
                db.add(conversation)
                await db.commit()
            
        except Exception as e:
            logger.error("Error processing query", error=str(e))
            await update.message.reply_text(
                "❌ I'm having trouble accessing your meeting history right now. Please try again later."
            )
    
    async def _get_or_create_user(self, db, telegram_user) -> User:
        """Get or create user in database"""
        from sqlalchemy import select
        
        # Try to find existing user
        result = await db.execute(
            select(User).where(User.telegram_id == telegram_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Create new user
            user = User(
                telegram_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info(f"Created new user: {telegram_user.id}")
        
        return user
    
    async def health_check(self):
        """Health check for the bot"""
        try:
            if self.bot:
                await self.bot.get_me()
                return True
            return False
        except Exception as e:
            logger.error("Bot health check failed", error=str(e))
            return False