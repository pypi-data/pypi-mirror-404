"""
Test configuration for Nemati AI SDK.
"""

import pytest


@pytest.fixture
def api_key():
    """Test API key."""
    return "nai_test_xxxxxxxxxxxx"


@pytest.fixture
def mock_response():
    """Factory for mock responses."""
    def _mock(data, status_code=200):
        return {
            "success": True,
            "data": data,
            "meta": {"request_id": "test_123"}
        }
    return _mock
