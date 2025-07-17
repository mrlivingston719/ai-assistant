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
from .telegram_bot import TelegramBot
from .ollama_client import OllamaClient

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
telegram_bot = None
ollama_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global vector_store, telegram_bot, ollama_client
    
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
        
        # Initialize Telegram bot
        telegram_bot = TelegramBot(vector_store, ollama_client)
        await telegram_bot.initialize()
        logger.info("Telegram bot initialized")
        
        # Start background tasks
        asyncio.create_task(telegram_bot.start_polling())
        
        logger.info("RovoDev application started successfully")
        
    except Exception as e:
        logger.error("Failed to initialize application", error=str(e))
        raise
    
    yield
    
    # Cleanup
    logger.info("Shutting down RovoDev application")
    if telegram_bot:
        await telegram_bot.stop()
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
        async with get_db() as db:
            await db.execute("SELECT 1")
        
        # Check vector store
        if vector_store:
            await vector_store.health_check()
        
        # Check Ollama
        if ollama_client:
            await ollama_client.health_check()
        
        return {
            "status": "healthy",
            "database": "connected",
            "vector_store": "connected",
            "ollama": "connected"
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
            "telegram": "python-telegram-bot"
        }
    }

@app.post("/webhook/telegram")
async def telegram_webhook(update: dict):
    """Telegram webhook endpoint"""
    if telegram_bot:
        await telegram_bot.handle_webhook(update)
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )