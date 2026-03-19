"""
Main FastAPI application for the conversation recorder backend.
"""

import os
import uuid
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.transcription import transcribe_audio

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

# Global storage for transcriptions (queued for the /next endpoint)
transcription_queue: List[Dict] = []
sent_transcriptions: set = set()


class TranscriptionResult(BaseModel):
    """Transcription result from speech-to-text."""
    text: str
    segments: List[Dict]
    language: str
    language_probability: float
    duration: float


class AudioUploadResponse(BaseModel):
    """Response model for audio upload."""
    success: bool
    message: str
    file_id: str
    filename: str
    file_size: int
    timestamp: str
    duration: Optional[str] = None
    transcription: Optional[TranscriptionResult] = None


class SuggestionResponse(BaseModel):
    """Response model for the /next endpoint — returns transcribed text."""
    success: bool
    suggestion: Optional[str] = None
    timestamp: Optional[str] = None
    suggestion_id: Optional[str] = None
    message: str
    transcription: Optional[TranscriptionResult] = None


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

        # Transcribe the audio (non-fatal if it fails)
        transcription_data = None
        try:
            result = transcribe_audio(file_path)
            transcription_data = TranscriptionResult(**result)
            print(f"--- Transcription Result ---")
            print(f"  Text: {transcription_data.text}")
            print(f"  Language: {transcription_data.language} ({transcription_data.language_probability})")
            print(f"  Duration: {transcription_data.duration}s")
            print(f"  Segments: {len(transcription_data.segments)}")
            for seg in transcription_data.segments:
                print(f"    [{seg.get('start', 0):.1f}s - {seg.get('end', 0):.1f}s] {seg.get('text', '')}")
            print(f"----------------------------")

            # Queue transcription for the /next endpoint
            transcription_queue.append({
                "id": str(uuid.uuid4()),
                "text": transcription_data.text,
                "timestamp": datetime.utcnow().isoformat(),
                "transcription": result,
                "sent": False,
            })
        except Exception as e:
            print(f"Transcription failed (non-fatal): {e}")

        # Log the upload
        print(f"Audio uploaded: {filename} ({file_size} bytes)")
        print(f"Timestamp: {timestamp}")
        print(f"Duration: {duration} seconds")

        return AudioUploadResponse(
            success=True,
            message="Audio file uploaded successfully",
            file_id=file_id,
            filename=filename,
            file_size=file_size,
            timestamp=timestamp,
            duration=duration,
            transcription=transcription_data,
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
    Get the next unsent transcription from the queue.

    Returns:
        SuggestionResponse with the transcribed text
    """
    try:
        # Find the next unsent transcription
        for entry in transcription_queue:
            if entry["id"] not in sent_transcriptions:
                # Mark as sent
                sent_transcriptions.add(entry["id"])
                entry["sent"] = True

                transcription_result = TranscriptionResult(**entry["transcription"])

                return SuggestionResponse(
                    success=True,
                    suggestion=entry["text"],
                    timestamp=entry["timestamp"],
                    suggestion_id=entry["id"],
                    message="Transcription retrieved successfully",
                    transcription=transcription_result,
                )

        # No new transcriptions available
        return SuggestionResponse(
            success=False,
            suggestion=None,
            timestamp=None,
            suggestion_id=None,
            message="No new transcriptions available"
        )

    except Exception as e:
        print(f"Error getting next transcription: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get next transcription: {str(e)}",
        )


@app.get("/api/suggestions/all")
async def get_all_suggestions():
    """Get all transcriptions (for debugging/testing purposes)."""
    try:
        return {
            "success": True,
            "suggestions": transcription_queue,
            "total_suggestions": len(transcription_queue),
            "sent_count": len(sent_transcriptions),
            "pending_count": len(transcription_queue) - len(sent_transcriptions)
        }

    except Exception as e:
        print(f"Error getting all transcriptions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get all transcriptions: {str(e)}",
        )


@app.post("/api/suggestions/reset")
async def reset_suggestions():
    """Reset the transcription queue (for testing purposes)."""
    try:
        global transcription_queue, sent_transcriptions
        transcription_queue.clear()
        sent_transcriptions.clear()

        return {
            "success": True,
            "message": "Transcription queue reset successfully"
        }

    except Exception as e:
        print(f"Error resetting transcriptions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset transcriptions: {str(e)}",
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
