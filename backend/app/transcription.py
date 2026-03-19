"""
Speech-to-text transcription service using faster-whisper.
"""

import logging
from pathlib import Path
from typing import Optional

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    WhisperModel = None

logger = logging.getLogger(__name__)

# Global model instance (loaded once, reused across requests)
_model = None


def get_model() -> WhisperModel:
    """Get or initialize the Whisper model (singleton)."""
    global _model
    if _model is None:
        logger.info("Loading Whisper model (base)... This may take a moment on first run.")
        # "base" is a good balance of speed vs accuracy.
        # Use "tiny" for faster but less accurate, "small"/"medium" for better accuracy.
        # compute_type="int8" keeps memory usage low on CPU.
        _model = WhisperModel("base", device="cpu", compute_type="int8")
        logger.info("Whisper model loaded successfully.")
    return _model


def transcribe_audio(file_path: Path) -> dict:
    """
    Transcribe an audio file to text.

    Args:
        file_path: Path to the audio file.

    Returns:
        Dict with "text" (full transcription), "segments" (timestamped segments),
        and "language" (detected language).
    """
    if not WHISPER_AVAILABLE:
        raise RuntimeError("faster-whisper is not installed. Install it with: pip install faster-whisper")

    model = get_model()

    segments_iter, info = model.transcribe(
        str(file_path),
        beam_size=5,
        vad_filter=False,
    )

    segments = []
    full_text_parts = []

    for segment in segments_iter:
        segments.append({
            "start": round(segment.start, 2),
            "end": round(segment.end, 2),
            "text": segment.text.strip(),
        })
        full_text_parts.append(segment.text.strip())

    full_text = " ".join(full_text_parts)

    return {
        "text": full_text,
        "segments": segments,
        "language": info.language,
        "language_probability": round(info.language_probability, 2),
        "duration": round(info.duration, 2),
    }
