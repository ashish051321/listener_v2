"""
Utility functions for the conversation recorder backend.
"""

import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile


def generate_file_id() -> str:
    """Generate a unique file ID."""
    return str(uuid.uuid4())


def generate_filename(file_id: str, original_filename: Optional[str] = None) -> str:
    """
    Generate a unique filename for the uploaded file.
    
    Args:
        file_id: Unique identifier for the file
        original_filename: Original filename (optional)
        
    Returns:
        Generated filename with extension
    """
    if original_filename:
        extension = Path(original_filename).suffix
    else:
        extension = ".webm"  # Default extension
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"conversation_{timestamp}_{file_id}{extension}"


def validate_audio_file(file: UploadFile, max_size: int = 50 * 1024 * 1024) -> None:
    """
    Validate uploaded audio file.
    
    Args:
        file: Uploaded file
        max_size: Maximum file size in bytes
        
    Raises:
        HTTPException: If file is invalid
    """
    # Check if file is provided
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Check file type
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Only audio files are allowed.",
        )
    
    # Check file size (if available)
    if hasattr(file, 'size') and file.size and file.size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {max_size / (1024 * 1024):.1f}MB",
        )


def calculate_file_hash(content: bytes) -> str:
    """
    Calculate SHA-256 hash of file content.
    
    Args:
        content: File content as bytes
        
    Returns:
        SHA-256 hash as hex string
    """
    return hashlib.sha256(content).hexdigest()


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"


def ensure_directory_exists(directory: Path) -> None:
    """
    Ensure a directory exists, create it if it doesn't.
    
    Args:
        directory: Directory path
    """
    directory.mkdir(parents=True, exist_ok=True)


def cleanup_old_files(directory: Path, max_age_days: int = 30) -> int:
    """
    Clean up old files from the uploads directory.
    
    Args:
        directory: Directory to clean
        max_age_days: Maximum age of files in days
        
    Returns:
        Number of files deleted
    """
    if not directory.exists():
        return 0
    
    cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)
    deleted_count = 0
    
    for file_path in directory.glob("conversation_*"):
        if file_path.stat().st_mtime < cutoff_time:
            try:
                file_path.unlink()
                deleted_count += 1
                print(f"Deleted old file: {file_path.name}")
            except Exception as e:
                print(f"Failed to delete {file_path.name}: {e}")
    
    return deleted_count
