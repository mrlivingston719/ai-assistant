"""
iOS Calendar integration service (.ics file generation)
"""

from datetime import datetime, timedelta
from typing import Optional
import uuid
import logging

from ..config import settings

logger = logging.getLogger(__name__)


class CalendarService:
    """Service for generating iOS Calendar .ics files"""
    
    def create_calendar_event(
        self, 
        title: str, 
        description: str = "", 
        due_date: datetime = None,
        reminder_minutes: int = None,
        requires_travel: bool = False,
        travel_time_minutes: int = 0
    ) -> str:
        """Create .ics calendar event content"""
        
        if not due_date:
            # Default to tomorrow if no due date specified
            due_date = datetime.now() + timedelta(days=1)
        
        # Calculate reminder time
        if reminder_minutes is None:
            reminder_minutes = settings.default_reminder_minutes
        
        # Add travel time if needed
        if requires_travel and travel_time_minutes > 0:
            reminder_minutes += travel_time_minutes
        
        # Calculate alarm time
        alarm_time = due_date - timedelta(minutes=reminder_minutes)
        
        # Generate unique UID
        event_uid = str(uuid.uuid4())
        
        # Format dates for .ics (UTC format)
        due_date_str = due_date.strftime('%Y%m%dT%H%M%SZ')
        alarm_time_str = alarm_time.strftime('%Y%m%dT%H%M%SZ')
        created_time = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        
        # Clean title and description for .ics format
        title_clean = self._clean_ics_text(title)
        description_clean = self._clean_ics_text(description)
        
        # Build .ics content
        ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//RovoDev//Personal AI Assistant//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
UID:{event_uid}@rovodev.local
DTSTART:{due_date_str}
DTEND:{due_date_str}
DTSTAMP:{created_time}
CREATED:{created_time}
SUMMARY:{title_clean}
DESCRIPTION:{description_clean}
STATUS:CONFIRMED
TRANSP:OPAQUE
BEGIN:VALARM
ACTION:DISPLAY
DESCRIPTION:Reminder: {title_clean}
TRIGGER:-PT{reminder_minutes}M
END:VALARM
END:VEVENT
END:VCALENDAR"""
        
        logger.info(f"Generated .ics event: {title} (reminder: {reminder_minutes} min)")
        return ics_content
    
    def create_meeting_reminder(
        self,
        meeting_title: str,
        meeting_date: datetime,
        location: str = None,
        reminder_minutes: int = None
    ) -> str:
        """Create .ics file for meeting reminder"""
        
        if reminder_minutes is None:
            reminder_minutes = settings.default_reminder_minutes
        
        # Add travel time if location is specified
        if location:
            reminder_minutes += 30  # Default 30 min travel buffer
        
        description = f"Meeting: {meeting_title}"
        if location:
            description += f"\nLocation: {location}"
        
        return self.create_calendar_event(
            title=f"Meeting: {meeting_title}",
            description=description,
            due_date=meeting_date,
            reminder_minutes=reminder_minutes,
            requires_travel=bool(location),
            travel_time_minutes=30 if location else 0
        )
    
    def create_action_item_reminder(
        self,
        action_title: str,
        due_date: datetime,
        description: str = "",
        priority: str = "medium",
        requires_travel: bool = False
    ) -> str:
        """Create .ics file for action item reminder"""
        
        # Adjust reminder time based on priority and travel
        reminder_minutes = settings.default_reminder_minutes
        
        if priority == "high":
            reminder_minutes = 60  # 1 hour for high priority
        elif priority == "low":
            reminder_minutes = 5   # 5 minutes for low priority
        
        if requires_travel:
            reminder_minutes += 30  # Add travel buffer
        
        # Add priority indicator to title
        priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "")
        title_with_priority = f"{priority_emoji} {action_title}" if priority_emoji else action_title
        
        return self.create_calendar_event(
            title=title_with_priority,
            description=description,
            due_date=due_date,
            reminder_minutes=reminder_minutes,
            requires_travel=requires_travel,
            travel_time_minutes=30 if requires_travel else 0
        )
    
    def create_deadline_reminder(
        self,
        deadline_title: str,
        deadline_date: datetime,
        description: str = "",
        urgency: str = "normal"
    ) -> str:
        """Create .ics file for deadline reminder"""
        
        # Multiple reminders for deadlines
        if urgency == "high":
            reminder_minutes = 120  # 2 hours before
        else:
            reminder_minutes = 60   # 1 hour before
        
        title_with_icon = f"⏰ Deadline: {deadline_title}"
        
        return self.create_calendar_event(
            title=title_with_icon,
            description=f"Deadline: {description}",
            due_date=deadline_date,
            reminder_minutes=reminder_minutes
        )
    
    def _clean_ics_text(self, text: str) -> str:
        """Clean text for .ics format compliance"""
        if not text:
            return ""
        
        # Replace problematic characters
        text = text.replace('\n', '\\n')
        text = text.replace('\r', '')
        text = text.replace(',', '\\,')
        text = text.replace(';', '\\;')
        text = text.replace('\\', '\\\\')
        
        # Limit length to avoid issues
        if len(text) > 200:
            text = text[:197] + "..."
        
        return text
    
    def get_filename_for_event(self, title: str) -> str:
        """Generate safe filename for .ics file"""
        # Clean title for filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')
        
        # Limit length
        if len(safe_title) > 50:
            safe_title = safe_title[:50]
        
        return f"{safe_title}.ics"