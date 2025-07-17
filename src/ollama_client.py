"""
Ollama Client for RovoDev
Handles LLM interactions with Ollama server
"""

import httpx
import structlog
import json
from typing import Dict, Any, List, Optional
import asyncio

from .config import settings

logger = structlog.get_logger()


class OllamaClient:
    """Client for interacting with Ollama LLM server"""
    
    def __init__(self):
        self.base_url = settings.ollama_url
        self.model = settings.ollama_model
        self.client = None
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize the Ollama client"""
        try:
            # Create HTTP client with longer timeout for LLM operations
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(60.0, connect=10.0),
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
            )
            
            # Test connection and model availability
            await self._verify_model()
            
            self.is_initialized = True
            logger.info("Ollama client initialized successfully", model=self.model)
            
        except Exception as e:
            logger.error("Failed to initialize Ollama client", error=str(e))
            raise
    
    async def _verify_model(self):
        """Verify that the required model is available"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            
            models_data = response.json()
            available_models = [model['name'] for model in models_data.get('models', [])]
            
            if self.model not in available_models:
                logger.warning(
                    "Model not found in available models", 
                    model=self.model, 
                    available=available_models
                )
                # Try to pull the model
                await self._pull_model()
            else:
                logger.info("Model verified", model=self.model)
                
        except Exception as e:
            logger.error("Failed to verify model", error=str(e))
            raise
    
    async def _pull_model(self):
        """Pull the required model"""
        try:
            logger.info("Pulling model", model=self.model)
            
            response = await self.client.post(
                f"{self.base_url}/api/pull",
                json={"name": self.model},
                timeout=300.0  # 5 minutes for model download
            )
            response.raise_for_status()
            
            logger.info("Model pulled successfully", model=self.model)
            
        except Exception as e:
            logger.error("Failed to pull model", error=str(e))
            raise
    
    async def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate response using Ollama"""
        if not self.is_initialized:
            raise RuntimeError("Ollama client not initialized")
        
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            logger.debug("Generating response", model=self.model, messages_count=len(messages))
            
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "top_k": 40
                    }
                }
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["message"]["content"]
            
            logger.debug("Response generated successfully", length=len(content))
            return content
            
        except httpx.TimeoutException:
            logger.error("Timeout generating response")
            return "I'm sorry, the response took too long to generate. Please try a shorter request."
        except httpx.HTTPStatusError as e:
            logger.error("HTTP error generating response", status=e.response.status_code)
            return "I'm experiencing technical difficulties. Please try again later."
        except Exception as e:
            logger.error("Error generating response", error=str(e))
            return "I'm sorry, I'm having trouble generating a response right now. Please try again later."
    
    async def extract_action_items(self, meeting_content: str) -> List[Dict[str, Any]]:
        """Extract action items from meeting content"""
        system_prompt = """You are an expert at extracting action items from meeting notes. 

Analyze the meeting content and extract action items in JSON format. For each action item, provide:
- title: Brief, clear title (required)
- description: More detailed description if available
- due_date: If mentioned, in ISO format (YYYY-MM-DD), otherwise null
- priority: "low", "medium", or "high" based on urgency
- requires_travel: true if the item mentions a location or travel
- assignee: person responsible if mentioned, otherwise null

Return only a valid JSON array of action items. If no action items found, return empty array [].

Example format:
[
  {
    "title": "Review quarterly budget",
    "description": "Analyze Q4 spending and prepare recommendations",
    "due_date": "2024-01-15",
    "priority": "high",
    "requires_travel": false,
    "assignee": "John Smith"
  }
]"""
        
        prompt = f"Meeting content:\n\n{meeting_content}"
        
        try:
            response = await self.generate_response(prompt, system_prompt)
            
            # Try to parse JSON response
            try:
                # Clean up response - sometimes models add extra text
                response = response.strip()
                if response.startswith('```json'):
                    response = response[7:]
                if response.endswith('```'):
                    response = response[:-3]
                response = response.strip()
                
                action_items = json.loads(response)
                
                if isinstance(action_items, list):
                    # Validate each action item
                    validated_items = []
                    for item in action_items:
                        if isinstance(item, dict) and 'title' in item:
                            # Ensure required fields
                            validated_item = {
                                'title': item.get('title', '').strip(),
                                'description': item.get('description', ''),
                                'due_date': item.get('due_date'),
                                'priority': item.get('priority', 'medium'),
                                'requires_travel': bool(item.get('requires_travel', False)),
                                'assignee': item.get('assignee')
                            }
                            
                            # Validate priority
                            if validated_item['priority'] not in ['low', 'medium', 'high']:
                                validated_item['priority'] = 'medium'
                            
                            if validated_item['title']:  # Only add if title exists
                                validated_items.append(validated_item)
                    
                    logger.info("Action items extracted", count=len(validated_items))
                    return validated_items
                else:
                    logger.warning("Action items response is not a list")
                    return []
                    
            except json.JSONDecodeError as e:
                logger.warning("Could not parse action items as JSON", error=str(e), response=response[:200])
                return []
                
        except Exception as e:
            logger.error("Error extracting action items", error=str(e))
            return []
    
    async def summarize_meeting(self, meeting_content: str) -> str:
        """Generate meeting summary"""
        system_prompt = """You are an expert at summarizing meetings. 

Create a concise, well-structured summary that includes:
- Key topics discussed
- Important decisions made
- Next steps or action items mentioned
- Any deadlines or dates mentioned

Keep the summary professional, focused on actionable information, and under 300 words.
Use bullet points for clarity when appropriate."""
        
        prompt = f"Please summarize this meeting:\n\n{meeting_content}"
        
        try:
            summary = await self.generate_response(prompt, system_prompt)
            logger.info("Meeting summary generated", length=len(summary))
            return summary
        except Exception as e:
            logger.error("Error summarizing meeting", error=str(e))
            return "Unable to generate meeting summary due to technical issues."
    
    async def categorize_meeting(self, meeting_content: str) -> str:
        """Categorize meeting type"""
        system_prompt = """Analyze the meeting content and categorize it as one of:
- work: Business meetings, project discussions, team meetings, client calls
- personal: Personal appointments, family meetings, social events, personal planning
- health: Medical appointments, therapy sessions, wellness discussions
- finance: Financial planning, investment discussions, budget meetings
- education: Learning sessions, training, courses, workshops
- other: Anything that doesn't fit the above categories

Respond with only the category name (lowercase, one word)."""
        
        # Use first 1000 characters for categorization to save tokens
        content_sample = meeting_content[:1000]
        if len(meeting_content) > 1000:
            content_sample += "..."
        
        prompt = f"Categorize this meeting:\n\n{content_sample}"
        
        try:
            category = await self.generate_response(prompt, system_prompt)
            category = category.strip().lower()
            
            valid_categories = ["work", "personal", "health", "finance", "education", "other"]
            if category in valid_categories:
                logger.info("Meeting categorized", category=category)
                return category
            else:
                logger.warning("Invalid category returned", category=category)
                return "other"
                
        except Exception as e:
            logger.error("Error categorizing meeting", error=str(e))
            return "other"
    
    async def answer_question_with_context(self, question: str, context: str) -> str:
        """Answer question using provided context"""
        system_prompt = """You are a helpful personal AI assistant. Use the provided context from the user's meetings and conversations to answer their question. 

Guidelines:
- If the context contains relevant information, use it to provide a specific, helpful answer
- If the context doesn't contain relevant information, say so clearly and offer to help in other ways
- Be conversational but professional
- Keep responses concise but complete
- If you mention specific meetings or dates, be precise
- Don't make up information that's not in the context"""
        
        prompt = f"""Context from previous meetings and conversations:
{context}

User question: {question}

Please provide a helpful response based on the context above."""
        
        try:
            response = await self.generate_response(prompt, system_prompt)
            logger.info("Question answered with context")
            return response
        except Exception as e:
            logger.error("Error answering question", error=str(e))
            return "I'm having trouble accessing the information right now. Please try again later."
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text (if supported by model)"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.model,
                    "prompt": text
                }
            )
            response.raise_for_status()
            
            result = response.json()
            embedding = result.get("embedding", [])
            
            if embedding:
                logger.debug("Embedding generated", dimensions=len(embedding))
                return embedding
            else:
                logger.warning("No embedding returned")
                return []
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning("Embedding endpoint not supported by model")
                return []
            else:
                logger.error("HTTP error generating embedding", status=e.response.status_code)
                return []
        except Exception as e:
            logger.error("Error generating embedding", error=str(e))
            return []
    
    async def health_check(self) -> bool:
        """Check if Ollama is healthy and model is available"""
        try:
            if not self.client:
                return False
            
            # Check if server is responding
            response = await self.client.get(f"{self.base_url}/api/tags", timeout=5.0)
            response.raise_for_status()
            
            # Check if our model is available
            models_data = response.json()
            available_models = [model['name'] for model in models_data.get('models', [])]
            
            is_healthy = self.model in available_models
            logger.debug("Health check completed", healthy=is_healthy, model_available=self.model in available_models)
            
            return is_healthy
            
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return False
    
    async def close(self):
        """Close the client connection"""
        try:
            if self.client:
                await self.client.aclose()
                self.client = None
            self.is_initialized = False
            logger.info("Ollama client closed")
        except Exception as e:
            logger.error("Error closing Ollama client", error=str(e))
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()