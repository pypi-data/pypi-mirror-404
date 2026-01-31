"""
Audio models for Nemati AI SDK.
"""

import base64
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class SpeechResponse:
    """Response from text-to-speech."""
    url: Optional[str] = None
    b64_data: Optional[str] = None
    format: str = "mp3"
    duration: Optional[float] = None
    credits: float = 0.0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpeechResponse":
        return cls(
            url=data.get("url"),
            b64_data=data.get("b64_data", data.get("audio")),
            format=data.get("format", "mp3"),
            duration=data.get("duration"),
            credits=data.get("credits", 0.0),
        )
    
    @property
    def content(self) -> bytes:
        """Get audio content as bytes."""
        if self.b64_data:
            return base64.b64decode(self.b64_data)
        elif self.url:
            import httpx
            response = httpx.get(self.url)
            return response.content
        return b""
    
    def save(self, path: str) -> None:
        """Save audio to file."""
        with open(path, "wb") as f:
            f.write(self.content)


@dataclass
class TranscriptionSegment:
    """A segment of transcription."""
    id: int
    text: str
    start: float
    end: float
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TranscriptionSegment":
        return cls(
            id=data.get("id", 0),
            text=data.get("text", ""),
            start=data.get("start", 0.0),
            end=data.get("end", 0.0),
        )


@dataclass
class TranscriptionResponse:
    """Response from speech-to-text."""
    text: str
    language: Optional[str] = None
    duration: Optional[float] = None
    segments: Optional[List[TranscriptionSegment]] = None
    credits: float = 0.0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TranscriptionResponse":
        segments_data = data.get("segments", [])
        segments = [TranscriptionSegment.from_dict(s) for s in segments_data] if segments_data else None
        
        return cls(
            text=data.get("text", ""),
            language=data.get("language"),
            duration=data.get("duration"),
            segments=segments,
            credits=data.get("credits", 0.0),
        )
    
    def __str__(self) -> str:
        return self.text
