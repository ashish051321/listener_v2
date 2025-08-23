"""
Pydantic models for the conversation recorder API.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class AudioUploadResponse(BaseModel):
    """Response model for audio upload."""
    success: bool = Field(..., description="Whether the upload was successful")
    message: str = Field(..., description="Response message")
    file_id: str = Field(..., description="Unique identifier for the uploaded file")
    filename: str = Field(..., description="Name of the saved file")
    file_size: int = Field(..., description="Size of the uploaded file in bytes")
    timestamp: str = Field(..., description="ISO timestamp of the recording")
    duration: Optional[str] = Field(None, description="Duration of the audio chunk in seconds")


class AudioFileInfo(BaseModel):
    """Model for audio file information."""
    filename: str = Field(..., description="Name of the audio file")
    size: int = Field(..., description="File size in bytes")
    created: str = Field(..., description="ISO timestamp when file was created")
    modified: str = Field(..., description="ISO timestamp when file was last modified")


class AudioFilesResponse(BaseModel):
    """Response model for listing audio files."""
    success: bool = Field(..., description="Whether the request was successful")
    files: List[AudioFileInfo] = Field(..., description="List of audio files")
    total_files: int = Field(..., description="Total number of files")
    total_size: int = Field(..., description="Total size of all files in bytes")


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Health status")
    timestamp: str = Field(..., description="ISO timestamp of the health check")
    version: str = Field(..., description="API version")


class ErrorResponse(BaseModel):
    """Response model for errors."""
    success: bool = Field(False, description="Always false for errors")
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
