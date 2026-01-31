"""
AI Writer resource for Nemati AI SDK.
"""

import json
from typing import Any, Dict, Iterator, List, Optional, Union

from ..models.writer import WriterResponse, WriterChunk


class Writer:
    """
    AI Writer resource.
    """
    
    def __init__(self, http_client):
        self._http = http_client
    
    def generate(
        self,
        prompt: str,
        content_type: str = "general",
        tone: str = "professional",
        max_tokens: Optional[int] = None,
        model: str = "gpt-4o-mini",
        language: str = "en",
        stream: bool = False,
        **kwargs,
    ) -> Union[WriterResponse, Iterator[WriterChunk]]:
        """Generate content using AI Writer."""
        payload = {
            "prompt": prompt,
            "content_type": content_type,
            "tone": tone,
            "model": model,
            "language": language,
            "stream": stream,
            **kwargs,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        if stream:
            return self._stream(payload)
        
        response = self._http.request("POST", "/writer/generate/", json=payload)
        return WriterResponse.from_dict(response.get("data", response))
    
    def _stream(self, payload: dict) -> Iterator[WriterChunk]:
        """Handle streaming response."""
        for line in self._http.stream("POST", "/writer/generate/", json=payload):
            if line.startswith("data: "):
                data = line[6:]
                if data.strip() == "[DONE]":
                    break
                try:
                    chunk_data = json.loads(data)
                    yield WriterChunk.from_dict(chunk_data)
                except json.JSONDecodeError:
                    continue
    
    def rewrite(
        self,
        text: str,
        instructions: str = "Improve this text",
        tone: Optional[str] = None,
        **kwargs,
    ) -> WriterResponse:
        """Rewrite existing text."""
        payload = {"text": text, "instructions": instructions, **kwargs}
        if tone:
            payload["tone"] = tone
        response = self._http.request("POST", "/writer/rewrite/", json=payload)
        return WriterResponse.from_dict(response.get("data", response))
    
    def summarize(
        self,
        text: str,
        length: str = "medium",
        **kwargs,
    ) -> WriterResponse:
        """Summarize text."""
        payload = {"text": text, "length": length, **kwargs}
        response = self._http.request("POST", "/writer/summarize/", json=payload)
        return WriterResponse.from_dict(response.get("data", response))
