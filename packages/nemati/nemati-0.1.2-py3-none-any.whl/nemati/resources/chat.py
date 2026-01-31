"""
Chat resource for Nemati AI SDK.
"""

import json
from typing import Dict, Iterator, List, Optional, Union

from ..models.chat import ChatResponse, ChatChunk, ChatMessage, Conversation


class Chat:
    """
    Chat completions resource.
    
    Create conversational AI interactions with various models.
    
    Usage:
        response = client.chat.create(
            messages=[{"role": "user", "content": "Hello!"}]
        )
        print(response.content)
        
        # Streaming
        for chunk in client.chat.create(messages=[...], stream=True):
            print(chunk.content, end="")
    """
    
    def __init__(self, http_client):
        self._http = http_client
        self.conversations = Conversations(http_client)
    
    def create(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4",
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 1.0,
        stream: bool = False,
        conversation_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> Union[ChatResponse, Iterator[ChatChunk]]:
        """
        Create a chat completion.
        
        Args:
            messages: List of messages with 'role' and 'content' keys.
                     Roles can be 'system', 'user', or 'assistant'.
            model: Model to use for completion. Defaults to 'gpt-4'.
            max_tokens: Maximum tokens in response. If None, uses model default.
            temperature: Sampling temperature (0-2). Higher = more creative.
            top_p: Nucleus sampling parameter.
            stream: Whether to stream the response.
            conversation_id: Optional conversation ID to continue a conversation.
            system_prompt: Optional system prompt (prepended to messages).
            **kwargs: Additional model-specific parameters.
        
        Returns:
            ChatResponse if stream=False, or Iterator[ChatChunk] if stream=True.
        
        Example:
            # Simple completion
            response = client.chat.create(
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "What is Python?"}
                ]
            )
            print(response.content)
            
            # Streaming
            for chunk in client.chat.create(
                messages=[{"role": "user", "content": "Write a poem"}],
                stream=True
            ):
                print(chunk.content, end="", flush=True)
        """
        # Build payload
        payload = {
            "messages": messages,
            "model": model,
            "temperature": temperature,
            "top_p": top_p,
            "stream": stream,
            **kwargs,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        if conversation_id:
            payload["conversation_id"] = conversation_id
        
        if system_prompt:
            # Prepend system message
            payload["messages"] = [
                {"role": "system", "content": system_prompt}
            ] + messages
        
        if stream:
            return self._stream(payload)
        
        response = self._http.request("POST", "/chat/completions/", json=payload)
        return ChatResponse.from_dict(response.get("data", response))
    
    def _stream(self, payload: dict) -> Iterator[ChatChunk]:
        """Handle streaming response."""
        for line in self._http.stream("POST", "/chat/completions/", json=payload):
            if line.startswith("data: "):
                data = line[6:]
                if data.strip() == "[DONE]":
                    break
                try:
                    chunk_data = json.loads(data)
                    yield ChatChunk.from_dict(chunk_data)
                except json.JSONDecodeError:
                    continue


class Conversations:
    """Manage chat conversations."""
    
    def __init__(self, http_client):
        self._http = http_client
    
    def create(
        self,
        title: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> Conversation:
        """
        Create a new conversation.
        
        Args:
            title: Optional title for the conversation.
            system_prompt: Optional system prompt for all messages.
        
        Returns:
            Conversation object with ID.
        """
        payload = {}
        if title:
            payload["title"] = title
        if system_prompt:
            payload["system_prompt"] = system_prompt
        
        response = self._http.request("POST", "/chat/conversations/", json=payload)
        return Conversation.from_dict(response.get("data", response))
    
    def list(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Conversation]:
        """
        List conversations.
        
        Args:
            limit: Maximum number of conversations to return.
            offset: Number of conversations to skip.
        
        Returns:
            List of Conversation objects.
        """
        response = self._http.request(
            "GET",
            "/chat/conversations/",
            params={"limit": limit, "offset": offset},
        )
        return [
            Conversation.from_dict(c)
            for c in response.get("data", response.get("items", []))
        ]
    
    def get(self, conversation_id: str) -> Conversation:
        """
        Get a specific conversation.
        
        Args:
            conversation_id: The conversation ID.
        
        Returns:
            Conversation object.
        """
        response = self._http.request("GET", f"/chat/conversations/{conversation_id}")
        return Conversation.from_dict(response.get("data", response))
    
    def delete(self, conversation_id: str) -> bool:
        """
        Delete a conversation.
        
        Args:
            conversation_id: The conversation ID.
        
        Returns:
            True if deleted successfully.
        """
        self._http.request("DELETE", f"/chat/conversations/{conversation_id}")
        return True
