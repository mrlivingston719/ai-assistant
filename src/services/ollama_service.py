"""
Ollama service for LLM interactions
"""

import httpx
import logging
from typing import Dict, Any, List
import json

from ..config import settings

logger = logging.getLogger(__name__)


class OllamaService:
    """Service for interacting with Ollama LLM"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.base_url = settings.ollama_host
        self.model = settings.ollama_model
    
    async def generate_response(self, prompt: str, system_prompt: str = None) -> str:
        """Generate response using Ollama"""
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False
                }
            )
            response.raise_for_status()
            
            result = response.json()
            return result["message"]["content"]
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I'm sorry, I'm having trouble generating a response right now. Please try again later."
    
    async def extract_action_items(self, meeting_content: str) -> List[Dict[str, Any]]:
        """Extract action items from meeting content"""
        system_prompt = """You are an expert at extracting action items from meeting notes. 
        
        Analyze the meeting content and extract action items in JSON format. For each action item, provide:
        - title: Brief, clear title
        - description: More detailed description if available
        - due_date: If mentioned, in ISO format (YYYY-MM-DD), otherwise null
        - priority: low, medium, or high
        - requires_travel: true if the item mentions a location or travel
        - assignee: person responsible if mentioned
        
        Return only valid JSON array of action items. If no action items found, return empty array []."""
        
        prompt = f"Meeting content:\n\n{meeting_content}"
        
        try:
            response = await self.generate_response(prompt, system_prompt)
            
            # Try to parse JSON response
            try:
                action_items = json.loads(response)
                if isinstance(action_items, list):
                    return action_items
                else:
                    logger.warning("Action items response is not a list")
                    return []
            except json.JSONDecodeError:
                logger.warning("Could not parse action items as JSON")
                return []
                
        except Exception as e:
            logger.error(f"Error extracting action items: {e}")
            return []
    
    async def summarize_meeting(self, meeting_content: str) -> str:
        """Generate meeting summary"""
        system_prompt = """You are an expert at summarizing meetings. 
        
        Create a concise, well-structured summary that includes:
        - Key topics discussed
        - Important decisions made
        - Next steps or action items
        - Any deadlines mentioned
        
        Keep the summary professional and focused on actionable information."""
        
        prompt = f"Please summarize this meeting:\n\n{meeting_content}"
        
        try:
            return await self.generate_response(prompt, system_prompt)
        except Exception as e:
            logger.error(f"Error summarizing meeting: {e}")
            return "Unable to generate meeting summary."
    
    async def categorize_meeting(self, meeting_content: str) -> str:
        """Categorize meeting type"""
        system_prompt = """Analyze the meeting content and categorize it as one of:
        - work: Business meetings, project discussions, team meetings
        - personal: Personal appointments, family meetings, social events
        - health: Medical appointments, therapy sessions
        - finance: Financial planning, investment discussions
        - education: Learning sessions, training, courses
        - other: Anything that doesn't fit the above categories
        
        Respond with only the category name (lowercase)."""
        
        prompt = f"Categorize this meeting:\n\n{meeting_content[:500]}..."
        
        try:
            category = await self.generate_response(prompt, system_prompt)
            category = category.strip().lower()
            
            valid_categories = ["work", "personal", "health", "finance", "education", "other"]
            if category in valid_categories:
                return category
            else:
                return "other"
                
        except Exception as e:
            logger.error(f"Error categorizing meeting: {e}")
            return "other"
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": settings.embedding_model,
                    "prompt": text
                }
            )
            response.raise_for_status()
            
            result = response.json()
            return result["embedding"]
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * 384
    
    async def answer_question_with_context(self, question: str, context: str) -> str:
        """Answer question using provided context"""
        system_prompt = """You are a helpful personal AI assistant. Use the provided context from the user's meetings and conversations to answer their question. 
        
        If the context contains relevant information, use it to provide a specific, helpful answer.
        If the context doesn't contain relevant information, say so and offer to help in other ways.
        
        Be conversational but professional. Keep responses concise but complete."""
        
        prompt = f"""Context from previous meetings:
{context}

Question: {question}"""
        
        try:
            return await self.generate_response(prompt, system_prompt)
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return "I'm having trouble accessing the information right now. Please try again later."
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.client:
            await self.client.aclose()