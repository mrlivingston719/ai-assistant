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

class User(Base):
    """User model for Telegram users"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Settings
    default_reminder_minutes = Column(Integer, default=15)
    timezone = Column(String(50), default="UTC")
    
    # Relationships
    meetings = relationship("Meeting", back_populates="user")
    action_items = relationship("ActionItem", back_populates="user")

class Meeting(Base):
    """Meeting model for processed meetings"""
    __tablename__ = "meetings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Meeting metadata
    title = Column(String(500), nullable=True)
    date = Column(DateTime(timezone=True), nullable=True)
    participants = Column(JSON, nullable=True)  # List of participant names
    meeting_type = Column(String(100), nullable=True)  # work, personal, etc.
    
    # Content
    transcript = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    
    # Source information
    source = Column(String(100), default="telegram")  # telegram, email, etc.
    source_id = Column(String(255), nullable=True)  # email ID, message ID, etc.
    
    # Vector storage reference
    vector_id = Column(String(255), nullable=True)  # ChromaDB document ID
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="meetings")
    action_items = relationship("ActionItem", back_populates="meeting")

class ActionItem(Base):
    """Action item model extracted from meetings"""
    __tablename__ = "action_items"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=True)
    
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
    
    # Notion integration
    notion_page_id = Column(String(255), nullable=True)
    
    # Vector storage reference
    vector_id = Column(String(255), nullable=True)  # ChromaDB document ID
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="action_items")
    meeting = relationship("Meeting", back_populates="action_items")

class Conversation(Base):
    """Conversation history with the AI assistant"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Message details
    message_type = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    
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
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
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