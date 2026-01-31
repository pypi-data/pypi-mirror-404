"""
HTTP client for Nemati AI SDK.
"""

import time
from typing import Any, Dict, Iterator, Optional

import httpx

from ._config import Config
from ._exceptions import (
    APIError,
    AuthenticationError,
    ConnectionError,
    InsufficientCreditsError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)


class HTTPClient:
    """Synchronous HTTP client with retry logic."""
    
    def __init__(self, config: Config):
        self.config = config
        self._client = httpx.Client(
            base_url=config.base_url,
            timeout=config.timeout,
            headers=self._default_headers(),
        )
    
    def _default_headers(self) -> Dict[str, str]:
        """Get default headers for all requests."""
        from ._version import __version__
        
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": f"nemati-python/{__version__}",
            "X-API-Key": self.config.api_key,
        }
    
    def request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic."""
        last_exception = None
        
        for attempt in range(self.config.max_retries):
            try:
                response = self._client.request(method, path, **kwargs)
                return self._handle_response(response)
            
            except httpx.TimeoutException:
                last_exception = TimeoutError()
                continue
            
            except httpx.ConnectError:
                last_exception = ConnectionError()
                continue
            
            except (RateLimitError, APIError) as e:
                # Don't retry on these errors unless it's a 5xx
                if isinstance(e, APIError) and e.status_code and e.status_code >= 500:
                    last_exception = e
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise
        
        if last_exception:
            raise last_exception
        
        raise ConnectionError("Failed after max retries")
    
    def stream(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> Iterator[str]:
        """Make streaming HTTP request."""
        try:
            with self._client.stream(method, path, **kwargs) as response:
                if response.status_code != 200:
                    # Read full response for error
                    response.read()
                    self._handle_error(response)
                
                for line in response.iter_lines():
                    if line:
                        yield line
        
        except httpx.TimeoutException:
            raise TimeoutError()
        except httpx.ConnectError:
            raise ConnectionError()
    
    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle HTTP response."""
        if response.status_code >= 400:
            self._handle_error(response)
        
        try:
            return response.json()
        except Exception:
            return {"raw": response.text}
    
    def _handle_error(self, response: httpx.Response) -> None:
        """Handle error response."""
        try:
            data = response.json()
            error = data.get("error", {})
            message = error.get("message", data.get("detail", "Unknown error"))
            error_code = error.get("code")
            request_id = data.get("meta", {}).get("request_id")
        except Exception:
            message = response.text or "Unknown error"
            error_code = None
            request_id = None
        
        status = response.status_code
        
        if status == 401:
            raise AuthenticationError(message)
        
        elif status == 402 or error_code == "insufficient_credits":
            details = error.get("details", {}) if isinstance(error, dict) else {}
            raise InsufficientCreditsError(
                message,
                required=details.get("required"),
                available=details.get("available"),
            )
        
        elif status == 422:
            errors = error.get("details", []) if isinstance(error, dict) else []
            raise ValidationError(message, errors=errors)
        
        elif status == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                message,
                retry_after=int(retry_after) if retry_after else None,
            )
        
        else:
            raise APIError(
                message,
                status_code=status,
                error_code=error_code,
                request_id=request_id,
            )
    
    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()
