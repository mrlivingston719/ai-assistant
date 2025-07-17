"""
Health check endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from datetime import datetime

from ..database import get_db_session
from ..config import settings

router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@router.get("/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db_session)):
    """Detailed health check including dependencies"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Check database
    try:
        await db.execute("SELECT 1")
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check ChromaDB
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://{settings.chromadb_host}:{settings.chromadb_port}/api/v1/heartbeat",
                timeout=5.0
            )
            if response.status_code == 200:
                health_status["services"]["chromadb"] = "healthy"
            else:
                health_status["services"]["chromadb"] = f"unhealthy: status {response.status_code}"
                health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["services"]["chromadb"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check Ollama
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.ollama_host}/api/tags",
                timeout=5.0
            )
            if response.status_code == 200:
                health_status["services"]["ollama"] = "healthy"
            else:
                health_status["services"]["ollama"] = f"unhealthy: status {response.status_code}"
                health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["services"]["ollama"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    return health_status