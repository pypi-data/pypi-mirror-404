"""
Nemati AI Synchronous Client.
"""

from typing import Optional

from ._config import Config
from ._http import HTTPClient
from .resources import (
    Chat,
    Writer,
    Image,
    Audio,
    Trends,
    Market,
    Documents,
    Account,
)


class NematiAI:
    """
    Nemati AI Python SDK Client.
    
    The main entry point for interacting with the Nemati AI API.
    
    Usage:
        client = NematiAI(api_key="your-api-key")
        
        # Chat
        response = client.chat.create(
            messages=[{"role": "user", "content": "Hello!"}]
        )
        
        # AI Writer
        content = client.writer.generate(
            prompt="Write a blog post",
            content_type="blog_post"
        )
        
        # Image Generation
        image = client.image.generate(
            prompt="A sunset over mountains"
        )
        
    Args:
        api_key: Your Nemati AI API key. If not provided, will look for
                 NEMATI_API_KEY environment variable.
        base_url: API base URL. Defaults to https://api.nemati.ai/v1/sdk
        timeout: Request timeout in seconds. Defaults to 60.
        max_retries: Maximum number of retries for failed requests. Defaults to 3.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.nemati.ai/v1/sdk",
        timeout: float = 60.0,
        max_retries: int = 3,
    ):
        self._config = Config(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        self._http = HTTPClient(self._config)
        
        # Initialize resources
        self.chat = Chat(self._http)
        self.writer = Writer(self._http)
        self.image = Image(self._http)
        self.audio = Audio(self._http)
        self.trends = Trends(self._http)
        self.market = Market(self._http)
        self.documents = Documents(self._http)
        self.account = Account(self._http)
    
    @property
    def is_test_mode(self) -> bool:
        """Check if client is using a test API key."""
        return self._config.is_test_key
    
    def close(self) -> None:
        """Close the client and release resources."""
        self._http.close()
    
    def __enter__(self) -> "NematiAI":
        return self
    
    def __exit__(self, *args) -> None:
        self.close()
    
    def __repr__(self) -> str:
        return f"NematiAI(base_url='{self._config.base_url}')"
