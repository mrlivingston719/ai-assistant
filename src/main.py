"""
RovoDev FastAPI Application
Main entry point for the personal AI assistant
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import structlog
import asyncio
from contextlib import asynccontextmanager

from .config import settings
from .database import init_db
from .vector_store import VectorStore
from .signal_bot import SignalBot, initialize_signal_bot
from .ollama_client import OllamaClient
from .routers import health, meetings, signal

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
vector_store = None
signal_bot = None
ollama_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global vector_store, signal_bot, ollama_client
    
    logger.info("Starting RovoDev application")
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized")
        
        # Initialize vector store
        vector_store = VectorStore()
        await vector_store.initialize()
        logger.info("Vector store initialized")
        
        # Initialize Ollama client
        ollama_client = OllamaClient()
        await ollama_client.initialize()
        logger.info("Ollama client initialized")
        
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
    if vector_store:
        await vector_store.close()
    if ollama_client:
        await ollama_client.close()

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
app.include_router(health.router, prefix="/health", tags=["health"])
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
        # Check database connection
        from .database import get_db
        from sqlalchemy import text
        async with get_db() as session:
            await session.execute(text("SELECT 1"))
        
        # Check vector store
        if vector_store:
            await vector_store.health_check()
        
        # Check Ollama
        if ollama_client:
            await ollama_client.health_check()
        
        # Check Signal bot
        signal_healthy = False
        if signal_bot:
            signal_healthy = await signal_bot.health_check()
        
        return {
            "status": "healthy",
            "database": "connected",
            "vector_store": "connected",
            "ollama": "connected",
            "signal": "connected" if signal_healthy else "disconnected"
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