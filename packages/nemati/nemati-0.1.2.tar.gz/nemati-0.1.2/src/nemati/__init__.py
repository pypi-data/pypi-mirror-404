"""
Nemati AI Python SDK

Official Python client for the Nemati AI API.

Usage:
    from nemati import NematiAI
    
    client = NematiAI(api_key="your-api-key")
    response = client.chat.create(messages=[{"role": "user", "content": "Hello!"}])
"""

from ._client import NematiAI
from ._async._client import AsyncNematiAI
from ._version import __version__
from ._exceptions import (
    NematiError,
    AuthenticationError,
    RateLimitError,
    InsufficientCreditsError,
    ValidationError,
    APIError,
    ConnectionError,
    TimeoutError,
)

__all__ = [
    "NematiAI",
    "AsyncNematiAI",
    "__version__",
    # Exceptions
    "NematiError",
    "AuthenticationError",
    "RateLimitError",
    "InsufficientCreditsError",
    "ValidationError",
    "APIError",
    "ConnectionError",
    "TimeoutError",
]
