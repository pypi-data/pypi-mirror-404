"""
Configuration management for Nemati AI SDK.
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class Config:
    """SDK Configuration."""
    
    api_key: Optional[str] = None
    base_url: str = "http://localhost:4600/auth/api/v1/sdk"
    timeout: float = 60.0
    max_retries: int = 3
    
    def __post_init__(self):
        # Try to get API key from environment if not provided
        if not self.api_key:
            self.api_key = os.environ.get("NEMATI_API_KEY")
        
        # Validate API key
        if not self.api_key:
            from ._exceptions import AuthenticationError
            raise AuthenticationError(
                "API key is required. Pass api_key parameter or set NEMATI_API_KEY environment variable."
            )
        
        # Validate API key format
        if not self.api_key.startswith("nai_"):
            from ._exceptions import AuthenticationError
            raise AuthenticationError(
                "Invalid API key format. API key should start with 'nai_'"
            )
        
        # Ensure base_url doesn't end with /
        self.base_url = self.base_url.rstrip("/")
    
    @property
    def is_test_key(self) -> bool:
        """Check if using a test API key."""
        return self.api_key.startswith("nai_test_") if self.api_key else False
    
    @property
    def is_live_key(self) -> bool:
        """Check if using a live API key."""
        return self.api_key.startswith("nai_live_") if self.api_key else False
