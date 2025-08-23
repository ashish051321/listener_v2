"""
Configuration settings for the conversation recorder backend.
"""

import os
from pathlib import Path
from typing import List

from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # API Settings
    api_title: str = "Conversation Recorder API"
    api_version: str = "1.0.0"
    api_description: str = "Backend API for recording and storing conversation audio files"
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    log_level: str = "info"
    
    # CORS Settings
    allowed_origins: List[str] = [
        "http://localhost:4200",  # Angular dev server
        "http://127.0.0.1:4200",
    ]
    
    # File Upload Settings
    uploads_dir: Path = Path("uploads")
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_audio_types: List[str] = [
        "audio/webm",
        "audio/mp4",
        "audio/wav",
        "audio/ogg",
    ]
    
    # Security Settings
    enable_rate_limiting: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # 1 hour
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Create settings instance
settings = Settings()

# Ensure uploads directory exists
settings.uploads_dir.mkdir(exist_ok=True)
