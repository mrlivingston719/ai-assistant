"""
Meeting management endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from ..database import get_db_session
from ..models import Meeting, ActionItem
from ..services.dependencies import get_meeting_processor, get_calendar_service
from ..services.meeting_processor import MeetingProcessor
from ..services.calendar_service import CalendarService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def get_meetings(
    skip: int = 0, 
    limit: int = 10, 
    meeting_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """Get list of meetings"""
    query = select(Meeting)
    
    if meeting_type:
        query = query.where(Meeting.meeting_type == meeting_type)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    meetings = result.scalars().all()
    
    return {
        "meetings": [
            {
                "id": m.id,
                "title": m.title,
                "meeting_date": m.meeting_date.isoformat() if m.meeting_date else None,
                "meeting_type": m.meeting_type,
                "processed": m.processed,
                "created_at": m.created_at.isoformat()
            }
            for m in meetings
        ]
    }


@router.get("/{meeting_id}")
async def get_meeting(meeting_id: int, db: AsyncSession = Depends(get_db_session)):
    """Get specific meeting details"""
    query = select(Meeting).where(Meeting.id == meeting_id)
    result = await db.execute(query)
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Get associated action items
    ai_query = select(ActionItem).where(ActionItem.meeting_id == meeting_id)
    ai_result = await db.execute(ai_query)
    action_items = ai_result.scalars().all()
    
    return {
        "meeting": {
            "id": meeting.id,
            "title": meeting.title,
            "content": meeting.content,
            "meeting_date": meeting.meeting_date.isoformat(),
            "participants": meeting.participants,
            "meeting_type": meeting.meeting_type,
            "source": meeting.source,
            "processed": meeting.processed,
            "created_at": meeting.created_at.isoformat()
        },
        "action_items": [
            {
                "id": ai.id,
                "title": ai.title,
                "description": ai.description,
                "due_date": ai.due_date.isoformat() if ai.due_date else None,
                "priority": ai.priority,
                "status": ai.status,
                "requires_travel": ai.requires_travel,
                "travel_time_minutes": ai.travel_time_minutes,
                "reminder_minutes": ai.reminder_minutes
            }
            for ai in action_items
        ]
    }


@router.post("/process")
async def process_meeting_content(
    content: str,
    title: Optional[str] = None,
    meeting_type: Optional[str] = "general",
    db: AsyncSession = Depends(get_db_session),
    meeting_processor: MeetingProcessor = Depends(get_meeting_processor)
):
    """Process meeting content and extract action items"""
    try:
        # Process the meeting
        result = await meeting_processor.process_meeting(
            content=content,
            title=title or "Manual Meeting Entry",
            meeting_type=meeting_type,
            db=db
        )
        
        return {
            "status": "success",
            "meeting_id": result["meeting_id"],
            "action_items_count": len(result["action_items"]),
            "summary": result["summary"]
        }
        
    except Exception as e:
        logger.error(f"Error processing meeting: {e}")
        raise HTTPException(status_code=500, detail="Failed to process meeting")


@router.get("/{meeting_id}/action-items")
async def get_meeting_action_items(meeting_id: int, db: AsyncSession = Depends(get_db_session)):
    """Get action items for a specific meeting"""
    query = select(Meeting).where(Meeting.id == meeting_id)
    result = await db.execute(query)
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    ai_query = select(ActionItem).where(ActionItem.meeting_id == meeting_id)
    ai_result = await db.execute(ai_query)
    action_items = ai_result.scalars().all()
    
    return {
        "meeting_id": meeting_id,
        "action_items": [
            {
                "id": ai.id,
                "title": ai.title,
                "description": ai.description,
                "due_date": ai.due_date.isoformat() if ai.due_date else None,
                "priority": ai.priority,
                "status": ai.status,
                "requires_travel": ai.requires_travel,
                "travel_time_minutes": ai.travel_time_minutes,
                "reminder_minutes": ai.reminder_minutes,
                "notion_page_id": ai.notion_page_id
            }
            for ai in action_items
        ]
    }


@router.post("/{meeting_id}/generate-calendar")
async def generate_calendar_files(
    meeting_id: int, 
    db: AsyncSession = Depends(get_db_session),
    calendar_service: CalendarService = Depends(get_calendar_service)
):
    """Generate .ics calendar files for meeting action items"""
    try:
        query = select(Meeting).where(Meeting.id == meeting_id)
        result = await db.execute(query)
        meeting = result.scalar_one_or_none()
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        ai_query = select(ActionItem).where(
            ActionItem.meeting_id == meeting_id,
            ActionItem.status == "pending",
            ActionItem.due_date.isnot(None)
        )
        ai_result = await db.execute(ai_query)
        action_items = ai_result.scalars().all()
        
        if not action_items:
            return {"message": "No pending action items with due dates found"}
        
        # Generate calendar files
        calendar_files = []
        for item in action_items:
            ics_content = calendar_service.create_calendar_event(
                title=item.title,
                description=item.description or "",
                due_date=item.due_date,
                reminder_minutes=item.reminder_minutes
            )
            
            calendar_files.append({
                "filename": f"{item.title.replace(' ', '_')}.ics",
                "content": ics_content,
                "action_item_id": item.id
            })
        
        return {
            "meeting_id": meeting_id,
            "calendar_files": calendar_files,
            "count": len(calendar_files)
        }
        
    except Exception as e:
        logger.error(f"Error generating calendar files: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate calendar files")


@router.get("/search")
async def search_meetings(
    query: str,
    limit: int = 5,
    db: AsyncSession = Depends(get_db_session)
):
    """Search meetings using vector similarity"""
    try:
        from ..vector_store import VectorStore
        
        vector_store = VectorStore()
        await vector_store.initialize()
        
        # Search for similar meetings
        results = await vector_store.search_similar(query, limit=limit, filter_type="meeting")
        
        # Get full meeting details
        meeting_details = []
        for result in results:
            meeting_id = result["metadata"].get("meeting_id")
            if meeting_id:
                meeting_query = select(Meeting).where(Meeting.id == meeting_id)
                meeting_result = await db.execute(meeting_query)
                meeting = meeting_result.scalar_one_or_none()
                if meeting:
                    meeting_details.append({
                        "meeting": {
                            "id": meeting.id,
                            "title": meeting.title,
                            "meeting_date": meeting.meeting_date.isoformat() if meeting.meeting_date else None,
                            "meeting_type": meeting.meeting_type
                        },
                        "relevance_score": 1.0 - result["distance"],  # Convert distance to similarity
                        "snippet": result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"]
                    })
        
        return {
            "query": query,
            "results": meeting_details,
            "count": len(meeting_details)
        }
        
    except Exception as e:
        logger.error(f"Error searching meetings: {e}")
        raise HTTPException(status_code=500, detail="Failed to search meetings")