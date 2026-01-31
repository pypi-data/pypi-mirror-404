"""
Chat models for Nemati AI SDK.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ChatMessage:
    """A chat message."""
    role: str
    content: str
    name: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatMessage":
        return cls(
            role=data.get("role", "user"),
            content=data.get("content", ""),
            name=data.get("name"),
        )


@dataclass
class ChatUsage:
    """Token usage information."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    credits: float = 0.0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatUsage":
        return cls(
            prompt_tokens=data.get("prompt_tokens", 0),
            completion_tokens=data.get("completion_tokens", 0),
            total_tokens=data.get("total_tokens", 0),
            credits=data.get("credits", 0.0),
        )


@dataclass
class ChatResponse:
    """Response from chat completion."""
    id: str
    content: str
    role: str = "assistant"
    model: str = ""
    finish_reason: Optional[str] = None
    usage: Optional[ChatUsage] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatResponse":
        content = data.get("content", "")
        if not content and "choices" in data:
            choices = data.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                content = message.get("content", "")
        
        usage_data = data.get("usage")
        usage = ChatUsage.from_dict(usage_data) if usage_data else None
        
        return cls(
            id=data.get("id", ""),
            content=content,
            role=data.get("role", "assistant"),
            model=data.get("model", ""),
            finish_reason=data.get("finish_reason"),
            usage=usage,
        )


@dataclass
class ChatChunk:
    """A chunk from streaming chat response."""
    id: str
    content: str
    role: str = "assistant"
    finish_reason: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatChunk":
        content = data.get("content", "")
        if not content and "choices" in data:
            choices = data.get("choices", [])
            if choices:
                delta = choices[0].get("delta", {})
                content = delta.get("content", "")
        
        return cls(
            id=data.get("id", ""),
            content=content,
            role=data.get("role", "assistant"),
            finish_reason=data.get("finish_reason"),
        )


@dataclass
class Conversation:
    """A chat conversation."""
    id: str
    title: Optional[str] = None
    system_prompt: Optional[str] = None
    message_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conversation":
        return cls(
            id=data.get("id", ""),
            title=data.get("title"),
            system_prompt=data.get("system_prompt"),
            message_count=data.get("message_count", 0),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
