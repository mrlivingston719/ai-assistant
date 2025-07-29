"""
Signal integration endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
import structlog

from ..signal_bot import get_signal_bot
from ..config import settings

router = APIRouter()
logger = structlog.get_logger()


@router.get("/status")
async def get_signal_status():
    """Get Signal bot status"""
    try:
        signal_bot = await get_signal_bot()
        
        if not signal_bot:
            return {
                "status": "not_initialized",
                "message": "Signal bot not initialized",
                "phone_number": settings.signal_phone_number
            }
        
        status = await signal_bot.get_status()
        return {
            "status": "active",
            "signal_bot_status": status,
            "phone_number": settings.signal_phone_number
        }
        
    except Exception as e:
        logger.error("Error getting Signal status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get Signal status")


@router.post("/send-message")
async def send_signal_message(message: str):
    """Send message via Signal (for testing)"""
    try:
        signal_bot = await get_signal_bot()
        
        if not signal_bot:
            raise HTTPException(status_code=503, detail="Signal bot not available")
        
        success = await signal_bot.signal_service.send_message(message)
        
        if success:
            return {"status": "sent", "message": "Message sent successfully"}
        else:
            return {"status": "failed", "message": "Failed to send message"}
            
    except Exception as e:
        logger.error("Error sending Signal message", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to send Signal message")


@router.post("/test-processing")
async def test_message_processing(content: str):
    """Test message processing (for development)"""
    try:
        signal_bot = await get_signal_bot()
        
        if not signal_bot:
            raise HTTPException(status_code=503, detail="Signal bot not available")
        
        response = await signal_bot.process_user_message(content)
        
        return {
            "status": "processed",
            "input": content[:100] + "..." if len(content) > 100 else content,
            "response": response
        }
        
    except Exception as e:
        logger.error("Error testing message processing", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to process test message")


@router.get("/health")
async def signal_health_check():
    """Health check for Signal integration"""
    try:
        signal_bot = await get_signal_bot()
        
        if not signal_bot:
            return {
                "healthy": False,
                "message": "Signal bot not initialized"
            }
        
        is_healthy = await signal_bot.health_check()
        
        return {
            "healthy": is_healthy,
            "signal_cli_configured": is_healthy,
            "phone_number": settings.signal_phone_number
        }
        
    except Exception as e:
        logger.error("Signal health check failed", error=str(e))
        return {
            "healthy": False,
            "error": str(e)
        }