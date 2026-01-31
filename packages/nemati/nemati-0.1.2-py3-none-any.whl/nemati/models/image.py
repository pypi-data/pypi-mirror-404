"""
Image models for Nemati AI SDK.
"""

import base64
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ImageUsage:
    """Usage information for image generation."""
    credits: float = 0.0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ImageUsage":
        return cls(credits=data.get("credits", 0.0))


@dataclass
class GeneratedImage:
    """A generated image."""
    url: Optional[str] = None
    b64_json: Optional[str] = None
    revised_prompt: Optional[str] = None
    model: str = ""
    size: str = ""
    usage: Optional[ImageUsage] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GeneratedImage":
        usage_data = data.get("usage")
        usage = ImageUsage.from_dict(usage_data) if usage_data else None
        
        return cls(
            url=data.get("url"),
            b64_json=data.get("b64_json"),
            revised_prompt=data.get("revised_prompt"),
            model=data.get("model", ""),
            size=data.get("size", ""),
            usage=usage,
        )
    
    @property
    def content(self) -> bytes:
        """Get image content as bytes."""
        if self.b64_json:
            return base64.b64decode(self.b64_json)
        elif self.url:
            import httpx
            response = httpx.get(self.url)
            return response.content
        return b""
    
    def save(self, path: str) -> None:
        """Save image to file."""
        with open(path, "wb") as f:
            f.write(self.content)
    
    def _repr_png_(self) -> bytes:
        """IPython/Jupyter representation."""
        return self.content


@dataclass
class ImageResponse:
    """Response from image generation (for multiple images)."""
    images: list
    model: str = ""
    usage: Optional[ImageUsage] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ImageResponse":
        images_data = data.get("data", data.get("images", []))
        images = [GeneratedImage.from_dict(img) for img in images_data]
        
        usage_data = data.get("usage")
        usage = ImageUsage.from_dict(usage_data) if usage_data else None
        
        return cls(
            images=images,
            model=data.get("model", ""),
            usage=usage,
        )
