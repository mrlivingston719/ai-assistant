"""
Calendar Service for RovoDev
Generates iOS-compatible .ics calendar files for action items and reminders
"""

import structlog
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from icalendar import Calendar, Event, vText
import uuid
import pytz
from dateutil import parser

from ..config import settings

logger = structlog.get_logger()


class CalendarService:
    """Service for creating iOS calendar files"""
    
    def __init__(self):
        self.default_timezone = pytz.timezone('UTC')
        
    async def create_reminder(
        self,
        title: str,
        description: str = "",
        due_date: Optional[str] = None,
        reminder_minutes: int = None,
        requires_travel: bool = False,
        location: str = None
    ) -> str:
        """Create an .ics calendar file for an action item reminder"""
        try:
            # Create calendar
            cal = Calendar()
            cal.add('prodid', '-//RovoDev//Personal AI Assistant//EN')
            cal.add('version', '2.0')
            cal.add('calscale', 'GREGORIAN')
            cal.add('method', 'PUBLISH')
            
            # Create event
            event = Event()
            
            # Set title
            event.add('summary', vText(title))
            
            # Set description
            if description:
                event.add('description', vText(description))
            
            # Set unique ID
            event.add('uid', str(uuid.uuid4()))
            
            # Set creation time
            now = datetime.now(self.default_timezone)
            event.add('dtstamp', now)
            event.add('created', now)
            
            # Parse and set due date
            if due_date:
                try:
                    # Parse the due date
                    if isinstance(due_date, str):
                        dt = parser.parse(due_date)
                    else:
                        dt = due_date
                    
                    # Ensure timezone awareness
                    if dt.tzinfo is None:
                        dt = self.default_timezone.localize(dt)
                    
                    # Set as all-day event if no time specified
                    if dt.hour == 0 and dt.minute == 0 and dt.second == 0:
                        event.add('dtstart', dt.date())
                        event.add('dtend', dt.date())
                    else:
                        event.add('dtstart', dt)
                        event.add('dtend', dt + timedelta(hours=1))  # 1-hour duration
                    
                except Exception as e:
                    logger.warning("Could not parse due date", due_date=due_date, error=str(e))
                    # Default to tomorrow at 9 AM
                    tomorrow = now + timedelta(days=1)
                    tomorrow = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
                    event.add('dtstart', tomorrow)
                    event.add('dtend', tomorrow + timedelta(hours=1))
            else:
                # Default to tomorrow at 9 AM
                tomorrow = now + timedelta(days=1)
                tomorrow = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
                event.add('dtstart', tomorrow)
                event.add('dtend', tomorrow + timedelta(hours=1))
            
            # Add location if provided
            if location:
                event.add('location', vText(location))
            
            # Set reminder
            reminder_minutes = reminder_minutes or settings.default_reminder_minutes
            
            # Add travel buffer if required
            if requires_travel:
                reminder_minutes += settings.travel_buffer_minutes
            
            # Create alarm
            from icalendar import Alarm
            alarm = Alarm()
            alarm.add('action', 'DISPLAY')
            alarm.add('description', f'Reminder: {title}')
            alarm.add('trigger', timedelta(minutes=-reminder_minutes))
            event.add_component(alarm)
            
            # Set priority based on travel requirement
            if requires_travel:
                event.add('priority', 5)  # High priority
            else:
                event.add('priority', 7)  # Normal priority
            
            # Add categories
            event.add('categories', vText('RovoDev,Action Item'))
            
            # Add to calendar
            cal.add_component(event)
            
            # Generate .ics content
            ics_content = cal.to_ical().decode('utf-8')
            
            logger.info("Calendar reminder created", title=title, due_date=due_date)
            return ics_content
            
        except Exception as e:
            logger.error("Error creating calendar reminder", error=str(e))
            raise
    
    async def create_meeting_reminder(
        self,
        title: str,
        meeting_date: datetime,
        duration_minutes: int = 60,
        participants: list = None,
        location: str = None,
        description: str = ""
    ) -> str:
        """Create a calendar event for a meeting"""
        try:
            # Create calendar
            cal = Calendar()
            cal.add('prodid', '-//RovoDev//Personal AI Assistant//EN')
            cal.add('version', '2.0')
            cal.add('calscale', 'GREGORIAN')
            cal.add('method', 'PUBLISH')
            
            # Create event
            event = Event()
            
            # Set title
            event.add('summary', vText(title))
            
            # Set description
            full_description = description
            if participants:
                full_description += f"\n\nParticipants: {', '.join(participants)}"
            
            if full_description:
                event.add('description', vText(full_description))
            
            # Set unique ID
            event.add('uid', str(uuid.uuid4()))
            
            # Set creation time
            now = datetime.now(self.default_timezone)
            event.add('dtstamp', now)
            event.add('created', now)
            
            # Ensure timezone awareness for meeting date
            if meeting_date.tzinfo is None:
                meeting_date = self.default_timezone.localize(meeting_date)
            
            # Set start and end times
            event.add('dtstart', meeting_date)
            event.add('dtend', meeting_date + timedelta(minutes=duration_minutes))
            
            # Add location if provided
            if location:
                event.add('location', vText(location))
            
            # Add attendees
            if participants:
                for participant in participants:
                    event.add('attendee', f'mailto:{participant}@example.com')
            
            # Set reminder (15 minutes before)
            from icalendar import Alarm
            alarm = Alarm()
            alarm.add('action', 'DISPLAY')
            alarm.add('description', f'Meeting reminder: {title}')
            alarm.add('trigger', timedelta(minutes=-15))
            event.add_component(alarm)
            
            # Add categories
            event.add('categories', vText('RovoDev,Meeting'))
            
            # Add to calendar
            cal.add_component(event)
            
            # Generate .ics content
            ics_content = cal.to_ical().decode('utf-8')
            
            logger.info("Meeting reminder created", title=title, date=meeting_date)
            return ics_content
            
        except Exception as e:
            logger.error("Error creating meeting reminder", error=str(e))
            raise
    
    async def create_deadline_reminder(
        self,
        title: str,
        deadline: datetime,
        description: str = "",
        priority: str = "medium"
    ) -> str:
        """Create a deadline reminder with multiple alerts"""
        try:
            # Create calendar
            cal = Calendar()
            cal.add('prodid', '-//RovoDev//Personal AI Assistant//EN')
            cal.add('version', '2.0')
            cal.add('calscale', 'GREGORIAN')
            cal.add('method', 'PUBLISH')
            
            # Create event
            event = Event()
            
            # Set title
            event.add('summary', vText(f"⏰ DEADLINE: {title}"))
            
            # Set description
            if description:
                event.add('description', vText(f"Deadline: {title}\n\n{description}"))
            
            # Set unique ID
            event.add('uid', str(uuid.uuid4()))
            
            # Set creation time
            now = datetime.now(self.default_timezone)
            event.add('dtstamp', now)
            event.add('created', now)
            
            # Ensure timezone awareness
            if deadline.tzinfo is None:
                deadline = self.default_timezone.localize(deadline)
            
            # Set as all-day event
            event.add('dtstart', deadline.date())
            event.add('dtend', deadline.date())
            
            # Set priority
            priority_map = {
                'low': 9,
                'medium': 5,
                'high': 1,
                'urgent': 1
            }
            event.add('priority', priority_map.get(priority, 5))
            
            # Add multiple reminders based on priority
            from icalendar import Alarm
            
            if priority in ['high', 'urgent']:
                # 1 week, 3 days, 1 day, 2 hours before
                reminder_times = [10080, 4320, 1440, 120]  # minutes
            elif priority == 'medium':
                # 3 days, 1 day, 4 hours before
                reminder_times = [4320, 1440, 240]
            else:  # low priority
                # 1 day, 2 hours before
                reminder_times = [1440, 120]
            
            for minutes_before in reminder_times:
                alarm = Alarm()
                alarm.add('action', 'DISPLAY')
                alarm.add('description', f'Deadline approaching: {title}')
                alarm.add('trigger', timedelta(minutes=-minutes_before))
                event.add_component(alarm)
            
            # Add categories
            event.add('categories', vText(f'RovoDev,Deadline,{priority.title()}'))
            
            # Add to calendar
            cal.add_component(event)
            
            # Generate .ics content
            ics_content = cal.to_ical().decode('utf-8')
            
            logger.info("Deadline reminder created", title=title, deadline=deadline, priority=priority)
            return ics_content
            
        except Exception as e:
            logger.error("Error creating deadline reminder", error=str(e))
            raise
    
    def generate_filename(self, title: str, event_type: str = "reminder") -> str:
        """Generate a safe filename for the .ics file"""
        try:
            # Clean title for filename
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title.replace(' ', '_')[:30]  # Limit length
            
            # Add timestamp for uniqueness
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            
            return f"{event_type}_{safe_title}_{timestamp}.ics"
            
        except Exception as e:
            logger.error("Error generating filename", error=str(e))
            return f"{event_type}_{datetime.now().strftime('%Y%m%d_%H%M')}.ics"
    
    async def create_multiple_reminders(self, action_items: list) -> list:
        """Create multiple calendar files for a list of action items"""
        try:
            calendar_files = []
            
            for item in action_items:
                try:
                    # Extract item details
                    title = item.get('title', 'Action Item')
                    description = item.get('description', '')
                    due_date = item.get('due_date')
                    requires_travel = item.get('requires_travel', False)
                    priority = item.get('priority', 'medium')
                    
                    # Skip items without due dates
                    if not due_date:
                        continue
                    
                    # Create appropriate reminder type
                    if priority in ['high', 'urgent']:
                        ics_content = await self.create_deadline_reminder(
                            title=title,
                            deadline=parser.parse(due_date),
                            description=description,
                            priority=priority
                        )
                    else:
                        ics_content = await self.create_reminder(
                            title=title,
                            description=description,
                            due_date=due_date,
                            requires_travel=requires_travel
                        )
                    
                    # Generate filename
                    filename = self.generate_filename(title, "action")
                    
                    calendar_files.append({
                        'content': ics_content,
                        'filename': filename,
                        'title': title
                    })
                    
                except Exception as e:
                    logger.error("Error creating reminder for item", item=item, error=str(e))
                    continue
            
            logger.info("Multiple reminders created", count=len(calendar_files))
            return calendar_files
            
        except Exception as e:
            logger.error("Error creating multiple reminders", error=str(e))
            return []