"""
Meeting processing service - core business logic
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Meeting, ActionItem
from ..vector_store import VectorStore
from ..ollama_client import OllamaClient
from .calendar_service import CalendarService
from .signal_service import SignalService
from ..config import settings

logger = logging.getLogger(__name__)


class MeetingProcessor:
    """Core service for processing meeting content"""
    
    def __init__(self, vector_store: VectorStore = None, ollama_client: OllamaClient = None):
        self.ollama_client = ollama_client or OllamaClient()
        self.calendar_service = CalendarService()
        self.signal_service = SignalService()
        self.vector_store = vector_store
    
    async def initialize(self):
        """Initialize vector store connection"""
        if not self.vector_store:
            self.vector_store = VectorStore()
            await self.vector_store.initialize()
    
    async def process_meeting(
        self, 
        content: str, 
        chat_id: str = None,
        title: str = None,
        meeting_type: str = None,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """Process meeting content and extract actionable information"""
        
        try:
            await self.initialize()
            
            # Generate title if not provided
            if not title:
                title = await self._generate_meeting_title(content)
            
            # Categorize meeting if type not provided
            if not meeting_type:
                meeting_type = await self.ollama_client.categorize_meeting(content)
            
            # Extract participants and date from content
            participants = self._extract_participants(content)
            meeting_date = self._extract_meeting_date(content)
            
            # Create meeting record
            meeting = Meeting(
                title=title,
                content=content,
                meeting_date=meeting_date,
                participants=participants,
                meeting_type=meeting_type,
                chat_id=chat_id or settings.signal_phone_number,
                source="signal" if chat_id else "manual",
                processed=False
            )
            
            if db:
                db.add(meeting)
                await db.commit()
                await db.refresh(meeting)
            
            # Store in vector database
            await self.vector_store.store_meeting(
                meeting_id=meeting.id,
                title=title,
                content=content,
                metadata={
                    "meeting_type": meeting_type,
                    "meeting_date": meeting_date.isoformat(),
                    "participants": participants
                }
            )
            
            # Extract action items
            action_items_data = await self.ollama_client.extract_action_items(content)
            action_items = []
            
            for item_data in action_items_data:
                action_item = await self._create_action_item(
                    item_data, meeting.id, db
                )
                if action_item:
                    action_items.append(action_item)
            
            # Generate meeting summary
            summary = await self.ollama_client.summarize_meeting(content)
            
            # Mark meeting as processed
            if db:
                meeting.processed = True
                await db.commit()
            
            # Generate calendar files for action items
            calendar_files = []
            for action_item in action_items:
                if action_item.due_date:
                    ics_content = self.calendar_service.create_action_item_reminder(
                        action_title=action_item.title,
                        due_date=action_item.due_date,
                        description=action_item.description or "",
                        priority=action_item.priority,
                        requires_travel=action_item.requires_travel
                    )
                    
                    filename = self.calendar_service.get_filename_for_event(action_item.title)
                    calendar_files.append({
                        "content": ics_content,
                        "filename": filename,
                        "action_item_id": action_item.id
                    })
            
            # Send calendar files via Signal if chat_id provided
            if chat_id and calendar_files:
                sent_count = await self.signal_service.send_multiple_calendar_files(
                    calendar_files
                )
                logger.info(f"Sent {sent_count} calendar files to Signal")
            
            # Prepare response
            result = {
                "meeting_id": meeting.id,
                "title": title,
                "meeting_type": meeting_type,
                "action_items": [
                    {
                        "id": ai.id,
                        "title": ai.title,
                        "description": ai.description,
                        "due_date": ai.due_date.isoformat() if ai.due_date else None,
                        "priority": ai.priority,
                        "status": ai.status
                    }
                    for ai in action_items
                ],
                "summary": summary,
                "calendar_files": calendar_files,
                "calendar_files_sent": len(calendar_files) if chat_id else 0
            }
            
            logger.info(f"Successfully processed meeting: {title}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing meeting: {e}")
            raise
    
    async def _generate_meeting_title(self, content: str) -> str:
        """Generate a meeting title from content"""
        try:
            system_prompt = """Generate a brief, descriptive title for this meeting based on the content. 
            The title should be 3-8 words and capture the main topic or purpose. 
            Examples: "Q1 Budget Review", "Team Standup", "Project Kickoff Meeting"
            
            Respond with only the title, no quotes or extra text."""
            
            prompt = f"Generate a title for this meeting:\n\n{content[:500]}..."
            
            title = await self.ollama_client.generate_response(prompt, system_prompt)
            title = title.strip().strip('"').strip("'")
            
            # Fallback if title is too long or empty
            if not title or len(title) > 100:
                return f"Meeting - {datetime.now().strftime('%Y-%m-%d')}"
            
            return title
            
        except Exception as e:
            logger.error(f"Error generating meeting title: {e}")
            return f"Meeting - {datetime.now().strftime('%Y-%m-%d')}"
    
    def _extract_participants(self, content: str) -> str:
        """Extract participants from meeting content"""
        # Simple extraction - look for common patterns
        participants = []
        
        # Look for patterns like "attendees:", "participants:", etc.
        lines = content.lower().split('\n')
        for line in lines:
            if any(keyword in line for keyword in ['attendee', 'participant', 'present', 'joined']):
                # Extract names after the keyword
                if ':' in line:
                    names_part = line.split(':', 1)[1].strip()
                    # Simple name extraction
                    names = [name.strip() for name in names_part.replace(',', ' ').split() 
                            if len(name.strip()) > 2 and name.strip().isalpha()]
                    participants.extend(names)
        
        return ', '.join(list(set(participants))) if participants else ""
    
    def _extract_meeting_date(self, content: str) -> datetime:
        """Extract meeting date from content"""
        # For now, default to current time
        # TODO: Implement date extraction logic
        return datetime.now()
    
    async def _create_action_item(
        self, 
        item_data: Dict[str, Any], 
        meeting_id: int, 
        db: AsyncSession
    ) -> Optional[ActionItem]:
        """Create action item from extracted data"""
        try:
            # Parse due date if provided
            due_date = None
            if item_data.get('due_date'):
                try:
                    due_date = datetime.fromisoformat(item_data['due_date'])
                except ValueError:
                    # If parsing fails, set to tomorrow
                    due_date = datetime.now() + timedelta(days=1)
            
            # Determine reminder time based on priority and travel
            reminder_minutes = settings.default_reminder_minutes
            requires_travel = item_data.get('requires_travel', False)
            priority = item_data.get('priority', 'medium')
            
            if priority == 'high':
                reminder_minutes = 60
            elif priority == 'low':
                reminder_minutes = 5
            
            travel_time = 30 if requires_travel else 0
            
            action_item = ActionItem(
                meeting_id=meeting_id,
                chat_id=settings.signal_phone_number,
                title=item_data.get('title', 'Untitled Action Item'),
                description=item_data.get('description', ''),
                due_date=due_date,
                priority=priority,
                status='pending',
                requires_travel=requires_travel,
                travel_time_minutes=travel_time,
                reminder_minutes=reminder_minutes + travel_time
            )
            
            if db:
                db.add(action_item)
                await db.commit()
                await db.refresh(action_item)
            
            return action_item
            
        except Exception as e:
            logger.error(f"Error creating action item: {e}")
            return None
    
    async def search_similar_meetings(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar meetings using vector search"""
        try:
            await self.initialize()
            
            results = await self.vector_store.search_similar(
                query, limit=limit, filter_type="meeting"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching similar meetings: {e}")
            return []
    
    async def get_meeting_context_for_query(self, query: str) -> str:
        """Get relevant meeting context for answering user queries"""
        try:
            await self.initialize()
            
            context = await self.vector_store.get_meeting_context(query)
            return context
            
        except Exception as e:
            logger.error(f"Error getting meeting context: {e}")
            return "No relevant meeting context found."
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.ollama_client:
            await self.ollama_client.cleanup()
        if self.signal_service:
            await self.signal_service.cleanup()
        if self.vector_store:
            await self.vector_store.cleanup()