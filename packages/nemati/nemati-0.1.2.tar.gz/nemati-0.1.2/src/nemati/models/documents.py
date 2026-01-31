"""
Documents models for Nemati AI SDK.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Document:
    """An uploaded document."""
    id: str
    name: str
    file_type: str = ""
    size: int = 0
    page_count: Optional[int] = None
    status: str = "ready"
    created_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            file_type=data.get("file_type", data.get("type", "")),
            size=data.get("size", 0),
            page_count=data.get("page_count", data.get("pages")),
            status=data.get("status", "ready"),
            created_at=data.get("created_at"),
        )


@dataclass
class DocumentSource:
    """A source reference in document chat."""
    page: int
    text: str
    relevance: float = 0.0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentSource":
        return cls(
            page=data.get("page", 0),
            text=data.get("text", ""),
            relevance=data.get("relevance", 0.0),
        )


@dataclass
class DocumentChatResponse:
    """Response from document chat."""
    answer: str
    conversation_id: Optional[str] = None
    sources: List[DocumentSource] = None
    credits: float = 0.0
    
    def __post_init__(self):
        if self.sources is None:
            self.sources = []
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentChatResponse":
        sources_data = data.get("sources", [])
        sources = [DocumentSource.from_dict(s) for s in sources_data]
        
        return cls(
            answer=data.get("answer", data.get("response", "")),
            conversation_id=data.get("conversation_id"),
            sources=sources,
            credits=data.get("credits", 0.0),
        )
    
    def __str__(self) -> str:
        return self.answer
