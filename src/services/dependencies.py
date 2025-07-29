"""
Service dependencies to avoid circular imports
"""

# Global instances (moved from main.py)
signal_bot = None
vector_store = None
ollama_client = None
meeting_processor = None
calendar_service = None

def get_meeting_processor():
    """Get meeting processor instance"""
    if meeting_processor is None:
        raise RuntimeError("Meeting processor not initialized")
    return meeting_processor

def get_calendar_service():
    """Get calendar service instance"""
    if calendar_service is None:
        raise RuntimeError("Calendar service not initialized")
    return calendar_service