"""
Meeting management endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from ..database import get_db, Meeting, ActionItem
from ..services.meeting_processor import MeetingProcessor
from ..services.calendar_service import CalendarService

router = APIRouter()
logger = logging.getLogger(__name__)

meeting_processor = MeetingProcessor()
calendar_service = CalendarService()


@router.get("/")
async def get_meetings(
    skip: int = 0, 
    limit: int = 10, 
    meeting_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get list of meetings"""
    query = db.query(Meeting)
    
    if meeting_type:
        query = query.filter(Meeting.meeting_type == meeting_type)
    
    meetings = query.offset(skip).limit(limit).all()
    
    return {
        "meetings": [
            {
                "id": m.id,
                "title": m.title,
                "meeting_date": m.meeting_date.isoformat(),
                "meeting_type": m.meeting_type,
                "processed": m.processed,
                "created_at": m.created_at.isoformat()
            }
            for m in meetings
        ]
    }


@router.get("/{meeting_id}")
async def get_meeting(meeting_id: int, db: Session = Depends(get_db)):
    """Get specific meeting details"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Get associated action items
    action_items = db.query(ActionItem).filter(ActionItem.meeting_id == meeting_id).all()
    
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
    db: Session = Depends(get_db)
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
async def get_meeting_action_items(meeting_id: int, db: Session = Depends(get_db)):
    """Get action items for a specific meeting"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    action_items = db.query(ActionItem).filter(ActionItem.meeting_id == meeting_id).all()
    
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
async def generate_calendar_files(meeting_id: int, db: Session = Depends(get_db)):
    """Generate .ics calendar files for meeting action items"""
    try:
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        action_items = db.query(ActionItem).filter(
            ActionItem.meeting_id == meeting_id,
            ActionItem.status == "pending",
            ActionItem.due_date.isnot(None)
        ).all()
        
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
    db: Session = Depends(get_db)
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
                meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
                if meeting:
                    meeting_details.append({
                        "meeting": {
                            "id": meeting.id,
                            "title": meeting.title,
                            "meeting_date": meeting.meeting_date.isoformat(),
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