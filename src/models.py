"""
SQLAlchemy database models for RovoDev
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional

Base = declarative_base()

# User model removed - using chat_id based approach for Signal integration

class Meeting(Base):
    """Meeting model for processed meetings"""
    __tablename__ = "meetings"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String(255), nullable=False)  # Signal phone number or Telegram chat ID
    
    # Meeting metadata
    title = Column(String(500), nullable=True)
    meeting_date = Column(DateTime(timezone=True), nullable=True)
    participants = Column(String(1000), nullable=True)  # Comma-separated participant names
    meeting_type = Column(String(100), nullable=True)  # work, personal, etc.
    
    # Content
    content = Column(Text, nullable=False)  # Meeting content/transcript
    summary = Column(Text, nullable=True)
    processed = Column(Boolean, default=False)
    
    # Source information
    source = Column(String(100), default="signal")  # signal, email, etc.
    source_id = Column(String(255), nullable=True)  # email ID, message ID, etc.
    
    # Vector storage reference
    vector_id = Column(String(255), nullable=True)  # ChromaDB document ID
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    action_items = relationship("ActionItem", back_populates="meeting")

class ActionItem(Base):
    """Action item model extracted from meetings"""
    __tablename__ = "action_items"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=True)
    chat_id = Column(String(255), nullable=False)  # Signal phone number or Telegram chat ID
    
    # Action item details
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    priority = Column(String(20), default="medium")  # low, medium, high, urgent
    
    # Status tracking
    status = Column(String(20), default="pending")  # pending, in_progress, completed, cancelled
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Calendar integration
    calendar_file_sent = Column(Boolean, default=False)
    reminder_minutes = Column(Integer, nullable=True)
    requires_travel = Column(Boolean, default=False)
    travel_time_minutes = Column(Integer, default=0)
    
    # Notion integration
    notion_page_id = Column(String(255), nullable=True)
    
    # Vector storage reference
    vector_id = Column(String(255), nullable=True)  # ChromaDB document ID
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    meeting = relationship("Meeting", back_populates="action_items")

class Conversation(Base):
    """Conversation history with the AI assistant"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String(255), nullable=False)  # Signal phone number or Telegram chat ID
    
    # Message details
    user_message = Column(Text, nullable=True)
    bot_response = Column(Text, nullable=True)
    message_type = Column(String(20), nullable=False)  # query, meeting, system
    processing_time = Column(Integer, nullable=True)  # Processing time in seconds
    
    # Context
    context_meetings = Column(JSON, nullable=True)  # List of meeting IDs used for context
    
    # Vector storage reference
    vector_id = Column(String(255), nullable=True)  # ChromaDB document ID
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ProcessingJob(Base):
    """Background job tracking"""
    __tablename__ = "processing_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String(255), nullable=False)  # Signal phone number or chat ID
    
    # Job details
    job_type = Column(String(100), nullable=False)  # meeting_processing, action_extraction, etc.
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    
    # Job data
    input_data = Column(JSON, nullable=True)
    result_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)