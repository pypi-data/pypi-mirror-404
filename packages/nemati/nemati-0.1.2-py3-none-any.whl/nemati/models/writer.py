"""
Writer models for Nemati AI SDK.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class WriterUsage:
    """Usage information for writer."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    credits: float = 0.0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WriterUsage":
        return cls(
            input_tokens=data.get("input_tokens", data.get("prompt_tokens", 0)),
            output_tokens=data.get("output_tokens", data.get("completion_tokens", 0)),
            total_tokens=data.get("total_tokens", 0),
            credits=data.get("credits", 0.0),
        )


@dataclass
class WriterResponse:
    """Response from AI Writer."""
    id: str
    text: str
    content_type: str = ""
    word_count: int = 0
    model: str = ""
    usage: Optional[WriterUsage] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WriterResponse":
        usage_data = data.get("usage")
        usage = WriterUsage.from_dict(usage_data) if usage_data else None
        text = data.get("text", data.get("content", ""))
        
        return cls(
            id=data.get("id", ""),
            text=text,
            content_type=data.get("content_type", ""),
            word_count=data.get("word_count", len(text.split()) if text else 0),
            model=data.get("model", ""),
            usage=usage,
        )
    
    def __str__(self) -> str:
        return self.text


@dataclass
class WriterChunk:
    """Streaming chunk from AI Writer."""
    text: str = ""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WriterChunk":
        return cls(
            text=data.get("text", ""),
        )


@dataclass
class TemplateVariable:
    """A template variable."""
    name: str
    description: str = ""
    type: str = "string"
    required: bool = True
    default: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateVariable":
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            type=data.get("type", "string"),
            required=data.get("required", True),
            default=data.get("default"),
        )


@dataclass
class Template:
    """An AI Writer template."""
    id: str
    name: str
    description: str = ""
    category: str = ""
    variables: List[TemplateVariable] = None
    
    def __post_init__(self):
        if self.variables is None:
            self.variables = []
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Template":
        variables = [
            TemplateVariable.from_dict(v)
            for v in data.get("variables", [])
        ]
        
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            category=data.get("category", ""),
            variables=variables,
        )