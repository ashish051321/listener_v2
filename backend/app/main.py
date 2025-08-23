"""
Main FastAPI application for the conversation recorder backend.
"""

import os
import uuid
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
import random

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Create uploads directory if it doesn't exist
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="Conversation Recorder API",
    description="Backend API for recording and storing conversation audio files",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Angular dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global storage for suggestions
suggestions: List[Dict] = []
sent_suggestions: set = set()

# Dummy suggestion templates
SUGGESTION_TEMPLATES = [
    "Consider asking about their experience with similar projects",
    "You might want to explore the technical challenges they've faced",
    "Ask about their team dynamics and collaboration methods",
    "Discuss the timeline and milestones they've set",
    "Explore their approach to problem-solving",
    "Ask about their communication strategies",
    "Consider discussing resource allocation and priorities",
    "You could explore their decision-making process",
    "Ask about their success metrics and KPIs",
    "Discuss their approach to risk management",
    "Consider exploring their innovation strategies",
    "Ask about their customer feedback mechanisms",
    "Discuss their quality assurance processes",
    "Explore their scalability considerations",
    "Ask about their competitive analysis approach"
]


class AudioUploadResponse(BaseModel):
    """Response model for audio upload."""
    success: bool
    message: str
    file_id: str
    filename: str
    file_size: int
    timestamp: str
    duration: Optional[str] = None


class SuggestionResponse(BaseModel):
    """Response model for suggestions."""
    success: bool
    suggestion: Optional[str] = None
    timestamp: Optional[str] = None
    suggestion_id: Optional[str] = None
    message: str


def generate_dummy_suggestions(audio_count: int) -> List[Dict]:
    """
    Generate dummy suggestions based on the number of audio files received.
    
    Args:
        audio_count: Number of audio files received so far
        
    Returns:
        List of suggestion dictionaries
    """
    new_suggestions = []
    
    # Generate 1-3 suggestions per audio file
    num_suggestions = min(audio_count, 3)
    
    for i in range(num_suggestions):
        suggestion_id = str(uuid.uuid4())
        suggestion_text = random.choice(SUGGESTION_TEMPLATES)
        timestamp = datetime.utcnow().isoformat()
        
        new_suggestions.append({
            "id": suggestion_id,
            "text": suggestion_text,
            "timestamp": timestamp,
            "audio_count": audio_count,
            "sent": False
        })
    
    return new_suggestions


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Conversation Recorder API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/api/audio/upload",
            "suggestions": "/api/suggestions/next",
            "files": "/api/audio/files",
            "health": "/health",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/api/audio/upload", response_model=AudioUploadResponse)
async def upload_audio(
    audio: UploadFile = File(..., description="Audio file to upload"),
    timestamp: str = Form(..., description="ISO timestamp of the recording"),
    duration: str = Form(..., description="Duration of the audio chunk in seconds"),
):
    """
    Upload an audio file from the conversation recorder.
    
    Args:
        audio: The audio file (WebM format)
        timestamp: ISO timestamp of when the recording was made
        duration: Duration of the audio chunk in seconds
        
    Returns:
        AudioUploadResponse with upload details
    """
    try:
        # Validate file type
        if not audio.content_type or not audio.content_type.startswith("audio/"):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only audio files are allowed.",
            )

        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = Path(audio.filename).suffix if audio.filename else ".webm"
        filename = f"conversation_{file_id}{file_extension}"
        
        # Save file to uploads directory
        file_path = UPLOADS_DIR / filename
        
        # Read and save the file
        content = await audio.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Get file size
        file_size = len(content)
        
        # Generate dummy suggestions based on total audio files
        total_files = len(list(UPLOADS_DIR.glob("conversation_*")))
        new_suggestions = generate_dummy_suggestions(total_files)
        suggestions.extend(new_suggestions)
        
        # Log the upload
        print(f"Audio uploaded: {filename} ({file_size} bytes)")
        print(f"Timestamp: {timestamp}")
        print(f"Duration: {duration} seconds")
        print(f"Generated {len(new_suggestions)} new suggestions")
        
        return AudioUploadResponse(
            success=True,
            message="Audio file uploaded successfully",
            file_id=file_id,
            filename=filename,
            file_size=file_size,
            timestamp=timestamp,
            duration=duration,
        )
        
    except Exception as e:
        print(f"Error uploading audio: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload audio file: {str(e)}",
        )


@app.get("/api/audio/files")
async def list_audio_files():
    """List all uploaded audio files."""
    try:
        files = []
        for file_path in UPLOADS_DIR.glob("conversation_*"):
            stat = file_path.stat()
            files.append({
                "filename": file_path.name,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
        
        # Sort by creation time (newest first)
        files.sort(key=lambda x: x["created"], reverse=True)
        
        return {
            "success": True,
            "files": files,
            "total_files": len(files),
            "total_size": sum(f["size"] for f in files),
        }
        
    except Exception as e:
        print(f"Error listing files: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list audio files: {str(e)}",
        )


@app.get("/api/suggestions/next", response_model=SuggestionResponse)
async def get_next_suggestion():
    """
    Get the next unsent suggestion from the queue.
    
    Returns:
        SuggestionResponse with the next suggestion
    """
    try:
        # Find the next unsent suggestion
        for suggestion in suggestions:
            if suggestion["id"] not in sent_suggestions:
                # Mark as sent
                sent_suggestions.add(suggestion["id"])
                suggestion["sent"] = True
                
                return SuggestionResponse(
                    success=True,
                    suggestion=suggestion["text"],
                    timestamp=suggestion["timestamp"],
                    suggestion_id=suggestion["id"],
                    message="Suggestion retrieved successfully"
                )
        
        # No more suggestions available
        return SuggestionResponse(
            success=False,
            suggestion=None,
            timestamp=None,
            suggestion_id=None,
            message="No more suggestions available"
        )
        
    except Exception as e:
        print(f"Error getting next suggestion: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get next suggestion: {str(e)}",
        )


@app.get("/api/suggestions/all")
async def get_all_suggestions():
    """
    Get all suggestions (for debugging/testing purposes).
    
    Returns:
        List of all suggestions with their status
    """
    try:
        return {
            "success": True,
            "suggestions": suggestions,
            "total_suggestions": len(suggestions),
            "sent_count": len(sent_suggestions),
            "pending_count": len(suggestions) - len(sent_suggestions)
        }
        
    except Exception as e:
        print(f"Error getting all suggestions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get all suggestions: {str(e)}",
        )


@app.post("/api/suggestions/reset")
async def reset_suggestions():
    """
    Reset the suggestion system (for testing purposes).
    
    Returns:
        Success message
    """
    try:
        global suggestions, sent_suggestions
        suggestions.clear()
        sent_suggestions.clear()
        
        return {
            "success": True,
            "message": "Suggestion system reset successfully"
        }
        
    except Exception as e:
        print(f"Error resetting suggestions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset suggestions: {str(e)}",
        )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
