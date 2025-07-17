"""
Telegram bot service
"""

import httpx
import logging
from typing import Optional, Dict, Any
import asyncio

from ..config import settings

logger = logging.getLogger(__name__)


class TelegramService:
    """Service for Telegram bot interactions"""
    
    def __init__(self):
        self.token = settings.telegram_bot_token
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def send_message(self, chat_id: str, text: str, parse_mode: str = "Markdown") -> bool:
        """Send text message to chat"""
        try:
            response = await self.client.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": parse_mode
                }
            )
            response.raise_for_status()
            
            logger.info(f"Message sent to chat {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending message to {chat_id}: {e}")
            return False
    
    async def send_document(self, chat_id: str, document_content: bytes, filename: str, caption: str = None) -> bool:
        """Send document to chat"""
        try:
            files = {
                "document": (filename, document_content, "application/octet-stream")
            }
            
            data = {
                "chat_id": chat_id
            }
            
            if caption:
                data["caption"] = caption
            
            response = await self.client.post(
                f"{self.base_url}/sendDocument",
                files=files,
                data=data
            )
            response.raise_for_status()
            
            logger.info(f"Document {filename} sent to chat {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending document to {chat_id}: {e}")
            return False
    
    async def send_calendar_file(self, chat_id: str, ics_content: str, filename: str) -> bool:
        """Send .ics calendar file to chat"""
        try:
            ics_bytes = ics_content.encode('utf-8')
            caption = "📅 Tap to add to your iOS Calendar"
            
            return await self.send_document(chat_id, ics_bytes, filename, caption)
            
        except Exception as e:
            logger.error(f"Error sending calendar file to {chat_id}: {e}")
            return False
    
    async def send_multiple_calendar_files(self, chat_id: str, calendar_files: list) -> int:
        """Send multiple calendar files with a summary message"""
        try:
            sent_count = 0
            
            # Send summary message first
            if len(calendar_files) > 1:
                await self.send_message(
                    chat_id, 
                    f"📅 I've created {len(calendar_files)} calendar reminders for you:"
                )
            
            # Send each calendar file
            for file_info in calendar_files:
                success = await self.send_calendar_file(
                    chat_id,
                    file_info["content"],
                    file_info["filename"]
                )
                if success:
                    sent_count += 1
                
                # Small delay between files to avoid rate limiting
                await asyncio.sleep(0.5)
            
            # Send completion message
            if sent_count > 0:
                await self.send_message(
                    chat_id,
                    f"✅ Sent {sent_count} calendar file(s). Tap any file to add to your iOS Calendar!"
                )
            
            return sent_count
            
        except Exception as e:
            logger.error(f"Error sending multiple calendar files: {e}")
            return 0
    
    async def set_webhook(self, webhook_url: str) -> bool:
        """Set webhook URL for the bot"""
        try:
            response = await self.client.post(
                f"{self.base_url}/setWebhook",
                json={
                    "url": webhook_url,
                    "allowed_updates": ["message"]
                }
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get("ok"):
                logger.info(f"Webhook set to {webhook_url}")
                return True
            else:
                logger.error(f"Failed to set webhook: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error setting webhook: {e}")
            return False
    
    async def delete_webhook(self) -> bool:
        """Delete webhook (switch to polling mode)"""
        try:
            response = await self.client.post(
                f"{self.base_url}/deleteWebhook"
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get("ok"):
                logger.info("Webhook deleted")
                return True
            else:
                logger.error(f"Failed to delete webhook: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting webhook: {e}")
            return False
    
    async def get_me(self) -> Optional[Dict[str, Any]]:
        """Get bot information"""
        try:
            response = await self.client.get(f"{self.base_url}/getMe")
            response.raise_for_status()
            
            result = response.json()
            if result.get("ok"):
                return result["result"]
            else:
                logger.error(f"Failed to get bot info: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting bot info: {e}")
            return None
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.client:
            await self.client.aclose()