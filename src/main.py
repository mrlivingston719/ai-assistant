"""
RovoDev FastAPI Application
Main entry point for the personal AI assistant
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import structlog
import asyncio
from contextlib import asynccontextmanager
from sqlalchemy import text

from .config import settings
from .database import init_db, get_db
from .vector_store import VectorStore
from .ollama_client import OllamaClient
from .signal_bot import SignalBot, initialize_signal_bot
from .services.meeting_processor import MeetingProcessor
from .services.calendar_service import CalendarService
from .routers import meetings, signal

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Global instances
signal_bot = None
vector_store = None
ollama_client = None
meeting_processor = None
calendar_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global signal_bot, vector_store, ollama_client
    
    logger.info("Starting RovoDev application")
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized")
        
        # Initialize vector store
        try:
            vector_store = VectorStore()
            await vector_store.initialize()
            logger.info("Vector store initialized")
        except Exception as e:
            logger.error("Vector store initialization failed", error=str(e))
            vector_store = None
        
        # Initialize Ollama client
        try:
            ollama_client = OllamaClient()
            await ollama_client.initialize()
            logger.info("Ollama client initialized")
        except Exception as e:
            logger.error("Ollama client initialization failed", error=str(e))
            ollama_client = None
        
        # Initialize services
        try:
            meeting_processor = MeetingProcessor(vector_store, ollama_client)
            await meeting_processor.initialize()
            logger.info("Meeting processor initialized")
        except Exception as e:
            logger.error("Meeting processor initialization failed", error=str(e))
            meeting_processor = None
        
        try:
            calendar_service = CalendarService()
            logger.info("Calendar service initialized")
        except Exception as e:
            logger.error("Calendar service initialization failed", error=str(e))
            calendar_service = None
        
        # Initialize Signal bot
        try:
            signal_bot = await initialize_signal_bot(vector_store, ollama_client)
            logger.info("Signal bot initialized")
        except Exception as e:
            logger.error("Signal bot initialization failed", error=str(e))
            logger.warning("Continuing without Signal bot - check Signal CLI configuration")
            signal_bot = None
        
        # Start background tasks
        if signal_bot:
            asyncio.create_task(signal_bot.start_monitoring())
        else:
            logger.warning("Signal bot not available - no message monitoring")
        
        logger.info("RovoDev application started successfully")
        
    except Exception as e:
        logger.error("Failed to initialize application", error=str(e))
        raise
    
    yield
    
    # Cleanup
    logger.info("Shutting down RovoDev application")
    if signal_bot:
        await signal_bot.stop()
    if meeting_processor:
        await meeting_processor.cleanup()
    if ollama_client:
        await ollama_client.close()
    if vector_store:
        await vector_store.close()

# Create FastAPI app
app = FastAPI(
    title="Personal AI Assistant",
    description="Local-first AI assistant for meeting processing and personal knowledge management",
    version="1.0.0",
    lifespan=lifespan
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(meetings.router, prefix="/meetings", tags=["meetings"])
app.include_router(signal.router, prefix="/signal", tags=["signal"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Personal AI Assistant",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker"""
    try:
        # Check database
        try:
            async with get_db() as session:
                await session.execute(text("SELECT 1"))
            db_status = "connected"
        except Exception:
            db_status = "disconnected"
        
        # Check services
        vector_status = "connected" if vector_store and hasattr(vector_store, 'client') else "disconnected"
        ollama_status = "connected" if ollama_client else "disconnected"
        signal_status = "connected" if signal_bot else "disconnected"
        
        overall_status = "healthy" if db_status == "connected" else "unhealthy"
        
        return {
            "status": overall_status,
            "database": db_status,
            "services": {
                "vector_store": vector_status,
                "ollama": ollama_status,
                "signal": signal_status
            }
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/status")
async def status():
    """Detailed status endpoint"""
    return {
        "application": "Personal AI Assistant",
        "version": "1.0.0",
        "environment": settings.environment,
        "debug": settings.debug,
        "components": {
            "database": "PostgreSQL",
            "vector_store": "ChromaDB",
            "llm": "Ollama + Qwen2.5-14B",
            "messaging": "Signal Note to Self"
        }
    }

# Service access functions for routers
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

# Signal integration handles messaging via Note to Self
# No webhook needed - uses polling for secure communication

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )