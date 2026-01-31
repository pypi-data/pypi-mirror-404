"""
Nemati AI SDK Exceptions

All exceptions that can be raised by the SDK.
"""

from typing import Any, Dict, List, Optional


class NematiError(Exception):
    """Base exception for all Nemati AI SDK errors."""
    
    def __init__(self, message: str, **kwargs: Any):
        self.message = message
        super().__init__(message)


class AuthenticationError(NematiError):
    """Raised when authentication fails (invalid or missing API key)."""
    
    def __init__(self, message: str = "Invalid or missing API key"):
        super().__init__(message)


class RateLimitError(NematiError):
    """Raised when rate limit is exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
    ):
        self.retry_after = retry_after
        super().__init__(message)
    
    def __str__(self) -> str:
        if self.retry_after:
            return f"{self.message}. Retry after {self.retry_after} seconds."
        return self.message


class InsufficientCreditsError(NematiError):
    """Raised when user doesn't have enough credits."""
    
    def __init__(
        self,
        message: str = "Insufficient credits",
        required: Optional[float] = None,
        available: Optional[float] = None,
    ):
        self.required = required
        self.available = available
        super().__init__(message)
    
    def __str__(self) -> str:
        if self.required and self.available is not None:
            return f"{self.message}. Required: {self.required}, Available: {self.available}"
        return self.message


class ValidationError(NematiError):
    """Raised when request validation fails."""
    
    def __init__(
        self,
        message: str = "Validation error",
        errors: Optional[List[Dict[str, Any]]] = None,
    ):
        self.errors = errors or []
        super().__init__(message)
    
    def __str__(self) -> str:
        if self.errors:
            error_details = "; ".join(
                f"{e.get('field', 'unknown')}: {e.get('message', 'invalid')}"
                for e in self.errors
            )
            return f"{self.message}: {error_details}"
        return self.message


class APIError(NematiError):
    """Raised when API returns an error response."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        request_id: Optional[str] = None,
    ):
        self.status_code = status_code
        self.error_code = error_code
        self.request_id = request_id
        super().__init__(message)
    
    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code:
            parts.insert(0, f"[{self.status_code}]")
        if self.error_code:
            parts.append(f"(code: {self.error_code})")
        return " ".join(parts)


class ConnectionError(NematiError):
    """Raised when connection to API fails."""
    
    def __init__(self, message: str = "Failed to connect to Nemati AI API"):
        super().__init__(message)


class TimeoutError(NematiError):
    """Raised when request times out."""
    
    def __init__(self, message: str = "Request timed out"):
        super().__init__(message)
