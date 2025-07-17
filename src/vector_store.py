"""
ChromaDB vector store integration
"""

import chromadb
from chromadb.config import Settings as ChromaSettings
import structlog
from typing import List, Dict, Any, Optional
import uuid

from .config import settings

logger = structlog.get_logger()

class VectorStore:
    """ChromaDB vector store client"""
    
    def __init__(self):
        self.client = None
        self.meetings_collection = None
        self.action_items_collection = None
        self.conversations_collection = None
    
    async def initialize(self):
        """Initialize ChromaDB client and collections"""
        try:
            # Create ChromaDB client
            self.client = chromadb.HttpClient(
                host=settings.chromadb_url.replace("http://", "").replace("https://", ""),
                port=8000,
                settings=ChromaSettings(
                    chroma_client_auth_provider="chromadb.auth.token.TokenAuthClientProvider",
                    chroma_client_auth_credentials=""
                )
            )
            
            # Create or get collections
            self.meetings_collection = self.client.get_or_create_collection(
                name="meetings",
                metadata={"description": "Meeting transcripts and summaries"}
            )
            
            self.action_items_collection = self.client.get_or_create_collection(
                name="action_items",
                metadata={"description": "Action items extracted from meetings"}
            )
            
            self.conversations_collection = self.client.get_or_create_collection(
                name="conversations",
                metadata={"description": "Conversation history with AI assistant"}
            )
            
            logger.info("Vector store initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize vector store", error=str(e))
            raise
    
    async def health_check(self):
        """Check if ChromaDB is healthy"""
        try:
            self.client.heartbeat()
            return True
        except Exception as e:
            logger.error("Vector store health check failed", error=str(e))
            raise
    
    async def store_meeting(
        self,
        meeting_id: int,
        content: str,
        metadata: Dict[str, Any],
        embedding: Optional[List[float]] = None
    ) -> str:
        """Store meeting in vector database"""
        try:
            vector_id = f"meeting_{meeting_id}_{uuid.uuid4().hex[:8]}"
            
            # Store in ChromaDB
            if embedding:
                self.meetings_collection.add(
                    documents=[content],
                    embeddings=[embedding],
                    metadatas=[metadata],
                    ids=[vector_id]
                )
            else:
                self.meetings_collection.add(
                    documents=[content],
                    metadatas=[metadata],
                    ids=[vector_id]
                )
            
            logger.info("Meeting stored in vector database", vector_id=vector_id)
            return vector_id
            
        except Exception as e:
            logger.error("Failed to store meeting in vector database", error=str(e))
            raise
    
    async def store_action_item(
        self,
        action_item_id: int,
        content: str,
        metadata: Dict[str, Any],
        embedding: Optional[List[float]] = None
    ) -> str:
        """Store action item in vector database"""
        try:
            vector_id = f"action_{action_item_id}_{uuid.uuid4().hex[:8]}"
            
            # Store in ChromaDB
            if embedding:
                self.action_items_collection.add(
                    documents=[content],
                    embeddings=[embedding],
                    metadatas=[metadata],
                    ids=[vector_id]
                )
            else:
                self.action_items_collection.add(
                    documents=[content],
                    metadatas=[metadata],
                    ids=[vector_id]
                )
            
            logger.info("Action item stored in vector database", vector_id=vector_id)
            return vector_id
            
        except Exception as e:
            logger.error("Failed to store action item in vector database", error=str(e))
            raise
    
    async def search_similar_meetings(
        self,
        query: str,
        user_id: int,
        limit: int = 5,
        embedding: Optional[List[float]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar meetings"""
        try:
            # Search in ChromaDB
            if embedding:
                results = self.meetings_collection.query(
                    query_embeddings=[embedding],
                    n_results=limit,
                    where={"user_id": user_id}
                )
            else:
                results = self.meetings_collection.query(
                    query_texts=[query],
                    n_results=limit,
                    where={"user_id": user_id}
                )
            
            # Format results
            similar_meetings = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    similar_meetings.append({
                        'content': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else None,
                        'id': results['ids'][0][i] if results['ids'] else None
                    })
            
            logger.info("Found similar meetings", count=len(similar_meetings))
            return similar_meetings
            
        except Exception as e:
            logger.error("Failed to search similar meetings", error=str(e))
            return []
    
    async def search_similar_action_items(
        self,
        query: str,
        user_id: int,
        limit: int = 5,
        embedding: Optional[List[float]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar action items"""
        try:
            # Search in ChromaDB
            if embedding:
                results = self.action_items_collection.query(
                    query_embeddings=[embedding],
                    n_results=limit,
                    where={"user_id": user_id}
                )
            else:
                results = self.action_items_collection.query(
                    query_texts=[query],
                    n_results=limit,
                    where={"user_id": user_id}
                )
            
            # Format results
            similar_items = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    similar_items.append({
                        'content': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else None,
                        'id': results['ids'][0][i] if results['ids'] else None
                    })
            
            logger.info("Found similar action items", count=len(similar_items))
            return similar_items
            
        except Exception as e:
            logger.error("Failed to search similar action items", error=str(e))
            return []
    
    async def store_conversation(
        self,
        conversation_id: int,
        content: str,
        metadata: Dict[str, Any],
        embedding: Optional[List[float]] = None
    ) -> str:
        """Store conversation in vector database"""
        try:
            vector_id = f"conv_{conversation_id}_{uuid.uuid4().hex[:8]}"
            
            # Store in ChromaDB
            if embedding:
                self.conversations_collection.add(
                    documents=[content],
                    embeddings=[embedding],
                    metadatas=[metadata],
                    ids=[vector_id]
                )
            else:
                self.conversations_collection.add(
                    documents=[content],
                    metadatas=[metadata],
                    ids=[vector_id]
                )
            
            logger.info("Conversation stored in vector database", vector_id=vector_id)
            return vector_id
            
        except Exception as e:
            logger.error("Failed to store conversation in vector database", error=str(e))
            raise
    
    async def close(self):
        """Close vector store connection"""
        # ChromaDB HTTP client doesn't need explicit closing
        logger.info("Vector store connection closed")