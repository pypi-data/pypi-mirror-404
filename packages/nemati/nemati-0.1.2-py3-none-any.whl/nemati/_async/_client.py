"""
Nemati AI Asynchronous Client.
"""

from typing import Optional

import httpx

from .._config import Config
from .._exceptions import (
    APIError,
    AuthenticationError,
    ConnectionError,
    InsufficientCreditsError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)


class AsyncHTTPClient:
    """Asynchronous HTTP client."""
    
    def __init__(self, config: Config):
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            from .._version import __version__
            
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": f"nemati-python/{__version__}",
                    "X-API-Key": self.config.api_key,
                },
            )
        return self._client
    
    async def request(self, method: str, path: str, **kwargs):
        client = await self._get_client()
        
        try:
            response = await client.request(method, path, **kwargs)
            return self._handle_response(response)
        except httpx.TimeoutException:
            raise TimeoutError()
        except httpx.ConnectError:
            raise ConnectionError()
    
    def _handle_response(self, response: httpx.Response):
        if response.status_code >= 400:
            self._handle_error(response)
        
        try:
            return response.json()
        except Exception:
            return {"raw": response.text}
    
    def _handle_error(self, response: httpx.Response):
        try:
            data = response.json()
            error = data.get("error", {})
            message = error.get("message", data.get("detail", "Unknown error"))
            error_code = error.get("code")
        except Exception:
            message = response.text or "Unknown error"
            error_code = None
        
        status = response.status_code
        
        if status == 401:
            raise AuthenticationError(message)
        elif status == 402 or error_code == "insufficient_credits":
            raise InsufficientCreditsError(message)
        elif status == 422:
            raise ValidationError(message)
        elif status == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(message, retry_after=int(retry_after) if retry_after else None)
        else:
            raise APIError(message, status_code=status, error_code=error_code)
    
    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None


class AsyncNematiAI:
    """
    Asynchronous Nemati AI Client.
    
    Usage:
        async with AsyncNematiAI(api_key="...") as client:
            response = await client.chat.create(messages=[...])
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
        self._http = AsyncHTTPClient(self._config)
        
        # Initialize async resources
        self.chat = AsyncChat(self._http)
        self.writer = AsyncWriter(self._http)
        self.image = AsyncImage(self._http)
        self.audio = AsyncAudio(self._http)
        self.trends = AsyncTrends(self._http)
        self.market = AsyncMarket(self._http)
        self.documents = AsyncDocuments(self._http)
        self.account = AsyncAccount(self._http)
    
    async def close(self):
        await self._http.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        await self.close()


# Async resource wrappers
class AsyncChat:
    def __init__(self, http):
        self._http = http
    
    async def create(self, messages, **kwargs):
        from ..models.chat import ChatResponse
        response = await self._http.request("POST", "/chat/completions", json={"messages": messages, **kwargs})
        return ChatResponse.from_dict(response.get("data", response))


class AsyncWriter:
    def __init__(self, http):
        self._http = http
    
    async def generate(self, prompt, **kwargs):
        from ..models.writer import WriterResponse
        response = await self._http.request("POST", "/writer/generate", json={"prompt": prompt, **kwargs})
        return WriterResponse.from_dict(response.get("data", response))


class AsyncImage:
    def __init__(self, http):
        self._http = http
    
    async def generate(self, prompt, **kwargs):
        from ..models.image import GeneratedImage
        response = await self._http.request("POST", "/image/generate", json={"prompt": prompt, **kwargs})
        return GeneratedImage.from_dict(response.get("data", response))


class AsyncAudio:
    def __init__(self, http):
        self._http = http


class AsyncTrends:
    def __init__(self, http):
        self._http = http
    
    async def search(self, query, **kwargs):
        from ..models.trends import TrendSearchResult
        response = await self._http.request("POST", "/trends/search", json={"query": query, **kwargs})
        return TrendSearchResult.from_dict(response.get("data", response))


class AsyncMarket:
    def __init__(self, http):
        self._http = http


class AsyncDocuments:
    def __init__(self, http):
        self._http = http


class AsyncAccount:
    def __init__(self, http):
        self._http = http
    
    async def me(self):
        from ..models.account import AccountInfo
        response = await self._http.request("GET", "/account/me")
        return AccountInfo.from_dict(response.get("data", response))
    
    async def credits(self):
        from ..models.account import Credits
        response = await self._http.request("GET", "/account/credits")
        return Credits.from_dict(response.get("data", response))
