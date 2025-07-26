"""
Configuration management for RovoDev
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    environment: str = Field(default="development")
    debug: bool = Field(default=True)
    log_level: str = Field(default="INFO")
    
    # Database
    database_url: str = Field(
        default="postgresql://assistant:password@localhost:5432/assistant",
        description="PostgreSQL database URL"
    )
    
    # Vector Database
    chromadb_url: str = Field(
        default="http://localhost:8000",
        description="ChromaDB server URL"
    )
    chromadb_host: str = Field(
        default="localhost",
        description="ChromaDB server host"
    )
    chromadb_port: int = Field(
        default=8000,
        description="ChromaDB server port"
    )
    
    # Ollama
    ollama_url: str = Field(
        default="http://localhost:11434",
        description="Ollama server URL"
    )
    ollama_host: str = Field(
        default="http://localhost:11434",
        description="Ollama server URL (alias for compatibility)"
    )
    ollama_model: str = Field(
        default="qwen2.5:14b",
        description="Ollama model to use"
    )
    embedding_model: str = Field(
        default="qwen2.5:14b",
        description="Model to use for embeddings"
    )
    
    # Signal
    signal_phone_number: Optional[str] = Field(
        default=None,
        description="Your Signal phone number (e.g., +1234567890)"
    )
    
    def validate_signal_config(self) -> bool:
        """Validate Signal configuration"""
        if not self.signal_phone_number:
            return False
        if not self.signal_phone_number.startswith('+'):
            return False
        if len(self.signal_phone_number) < 10:
            return False
        # Check for valid phone number format (+1234567890)
        import re
        if not re.match(r'^\+\d{10,15}$', self.signal_phone_number):
            return False
        return True
    signal_cli_path: str = Field(
        default="/usr/local/bin/signal-cli",
        description="Path to signal-cli executable"
    )
    
    # Notion
    notion_token: Optional[str] = Field(
        default=None,
        description="Notion integration token"
    )
    
    # Gmail
    gmail_credentials: Optional[str] = Field(
        default=None,
        description="Gmail API credentials JSON"
    )
    
    # Calendar settings
    default_reminder_minutes: int = Field(
        default=15,
        description="Default reminder time in minutes"
    )
    travel_buffer_minutes: int = Field(
        default=30,
        description="Travel buffer time in minutes"
    )
    
    # Application settings
    max_meeting_length: int = Field(
        default=10000,
        description="Maximum meeting text length to process"
    )
    max_context_meetings: int = Field(
        default=5,
        description="Maximum number of meetings to use for context"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Global settings instance
settings = Settings()