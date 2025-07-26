"""
Signal service for secure communication via Note to Self
"""

import asyncio
import subprocess
import logging
import json
import os
import tempfile
from typing import Optional, Dict, Any, List
from pathlib import Path

from ..config import settings

logger = logging.getLogger(__name__)


class SignalService:
    """Service for Signal Note to Self interactions"""
    
    def __init__(self):
        self.phone_number = settings.signal_phone_number
        self.signal_cli_path = settings.signal_cli_path
        self.is_monitoring = False
        
    async def send_message(self, message: str) -> bool:
        """Send message to Note to Self"""
        try:
            cmd = [
                self.signal_cli_path,
                "-a", self.phone_number,
                "send",
                self.phone_number,
                "-m", message
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info("Message sent to Note to Self")
                return True
            else:
                logger.error(f"Failed to send message: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    async def send_file(self, file_path: str, caption: str = None) -> bool:
        """Send file to Note to Self"""
        try:
            cmd = [
                self.signal_cli_path,
                "-a", self.phone_number,
                "send",
                self.phone_number,
                "-a", file_path
            ]
            
            if caption:
                cmd.extend(["-m", caption])
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"File {file_path} sent to Note to Self")
                return True
            else:
                logger.error(f"Failed to send file: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending file: {e}")
            return False
    
    async def send_calendar_file(self, ics_content: str, filename: str) -> bool:
        """Send .ics calendar file to Note to Self"""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ics', delete=False) as f:
                f.write(ics_content)
                temp_path = f.name
            
            try:
                caption = "📅 Tap to add to your iOS Calendar"
                success = await self.send_file(temp_path, caption)
                return success
            finally:
                # Clean up temporary file
                os.unlink(temp_path)
                
        except Exception as e:
            logger.error(f"Error sending calendar file: {e}")
            return False
    
    async def send_multiple_calendar_files(self, calendar_files: List[Dict[str, str]]) -> int:
        """Send multiple calendar files with a summary message"""
        try:
            sent_count = 0
            
            # Send summary message first
            if len(calendar_files) > 1:
                await self.send_message(
                    f"📅 I've created {len(calendar_files)} calendar reminders for you:"
                )
            
            # Send each calendar file
            for file_info in calendar_files:
                success = await self.send_calendar_file(
                    file_info["content"],
                    file_info["filename"]
                )
                if success:
                    sent_count += 1
                
                # Small delay between files
                await asyncio.sleep(0.5)
            
            # Send completion message
            if sent_count > 0:
                await self.send_message(
                    f"✅ Sent {sent_count} calendar file(s). Tap any file to add to your iOS Calendar!"
                )
            
            return sent_count
            
        except Exception as e:
            logger.error(f"Error sending multiple calendar files: {e}")
            return 0
    
    async def receive_messages(self) -> List[Dict[str, Any]]:
        """Receive new messages from Signal"""
        try:
            cmd = [
                self.signal_cli_path,
                "-a", self.phone_number,
                "receive",
                "--json"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                messages = []
                for line in stdout.decode().strip().split('\n'):
                    if line.strip():
                        try:
                            message_data = json.loads(line)
                            # Filter for messages from yourself (Note to Self)
                            if (message_data.get('envelope', {}).get('source') == self.phone_number and
                                message_data.get('envelope', {}).get('dataMessage', {}).get('message')):
                                messages.append(message_data)
                        except json.JSONDecodeError:
                            continue
                return messages
            else:
                logger.error(f"Failed to receive messages: {stderr.decode()}")
                return []
                
        except Exception as e:
            logger.error(f"Error receiving messages: {e}")
            return []
    
    async def start_monitoring(self, message_handler):
        """Start monitoring for new messages"""
        self.is_monitoring = True
        logger.info("Starting Signal message monitoring...")
        
        while self.is_monitoring:
            try:
                messages = await self.receive_messages()
                
                for message_data in messages:
                    try:
                        envelope = message_data.get('envelope', {})
                        data_message = envelope.get('dataMessage', {})
                        message_text = data_message.get('message', '')
                        timestamp = envelope.get('timestamp', 0)
                        
                        if message_text:
                            # Process the message
                            await message_handler(message_text, timestamp)
                            
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                
                # Wait before checking for new messages
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error in message monitoring: {e}")
                await asyncio.sleep(5)
    
    def stop_monitoring(self):
        """Stop monitoring for messages"""
        self.is_monitoring = False
        logger.info("Stopped Signal message monitoring")
    
    async def check_signal_cli(self) -> bool:
        """Check if signal-cli is installed and configured"""
        try:
            # Check if signal-cli exists
            if not os.path.exists(self.signal_cli_path):
                logger.error("signal-cli not found. Please install signal-cli first.")
                return False
            
            # Check if account is registered
            cmd = [self.signal_cli_path, "-a", self.phone_number, "listIdentities"]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info("Signal CLI is configured and ready")
                return True
            else:
                logger.error(f"Signal CLI not configured: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking signal-cli: {e}")
            return False
    
    async def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get Signal account information"""
        try:
            cmd = [self.signal_cli_path, "-a", self.phone_number, "listIdentities"]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return {
                    "phone_number": self.phone_number,
                    "status": "connected",
                    "identities": stdout.decode().strip()
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None
    
    async def cleanup(self):
        """Cleanup resources"""
        self.stop_monitoring()
        logger.info("Signal service cleaned up")